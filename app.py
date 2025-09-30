import math
from flask import Flask, request, render_template, send_file, Response, url_for
import io, base64, os, json, traceback
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import folium
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

from src.data_loader import load_growth_curves, load_species_master
from src.model import agb_from_chave, total_biomass_kg, biomass_to_co2
from src.climate import climate_at_latlon  # <-- climate sampler (WorldClim)

# Use explicit folders
app = Flask(__name__, template_folder="templates", static_folder="static")

# ---------- Data load ----------
def _safe_load_data():
    try:
        df_growth = load_growth_curves()
        print("[DATA] growth loaded:", getattr(df_growth, "shape", None))
    except Exception as e:
        print("[DATA] ERROR growth:", e)
        traceback.print_exc()
        df_growth = None

    try:
        df_species = load_species_master()
        print("[DATA] species loaded:", getattr(df_species, "shape", None))
    except Exception as e:
        print("[DATA] ERROR species:", e)
        traceback.print_exc()
        df_species = None

    return df_growth, df_species

DF_GROWTH, DF_SPECIES = _safe_load_data()
SPECIES_LIST = sorted(DF_SPECIES["species"].dropna().unique().tolist()) if (DF_SPECIES is not None and "species" in DF_SPECIES.columns) else []

# ---------- Core model (with optional climate scaling) ----------
def compute_curve(species: str, years: int, trees: int, lat=None, lon=None):
    if DF_GROWTH is None or DF_SPECIES is None:
        return None, "Datasets failed to load."

    if "species_scientific" not in DF_GROWTH.columns:
        return None, "Column 'species_scientific' missing in growth dataset."

    g = DF_GROWTH[DF_GROWTH["species_scientific"] == species].copy()
    if g.empty:
        return None, f"No growth records for '{species}'."

    if "age_years" not in g.columns or "dbh_cm" not in g.columns or "height_m" not in g.columns:
        return None, "Growth dataset missing one of: age_years, dbh_cm, height_m."

    g = g[g["age_years"] <= years].copy()
    if g.empty:
        return None, f"No growth records ≤ {years} years for '{species}'."

    srow = DF_SPECIES[DF_SPECIES["species"] == species]
    if srow.empty:
        return None, f"Species '{species}' not found in species master."
    srow = srow.iloc[0]

    rho  = float(srow.get("wood_density_g_cm3", 0.6))
    CF   = float(srow.get("carbon_fraction_CF", 0.47))
    R    = float(srow.get("root_to_shoot_ratio_R", 0.27))
    surv = float(srow.get("annual_survival_rate", 0.95))

    # biomass
    agb = agb_from_chave(g["dbh_cm"].values, g["height_m"].values, rho)  # kg per tree
    total_biomass = total_biomass_kg(agb, R)  # kg per tree

    # survival
    ages = g["age_years"].values.astype(int)
    alive = np.array([trees * (surv ** t) for t in ages])

    # CO2
    co2_per_tree = biomass_to_co2(total_biomass, CF)     # kg per tree
    co2_total_kg = co2_per_tree * alive                  # kg plantation that year
    co2_total_t  = co2_total_kg / 1000.0                 # tons
    co2_cum_t    = np.cumsum(co2_total_t)

    out = pd.DataFrame({
        "species": species,
        "age_years": ages,
        "trees_alive": alive,
        "CO2_tons": co2_total_t,
        "CO2_cumulative_tons": co2_cum_t
    })

    # ---- Climate scaling if lat/lon given ----
    if (lat is not None) and (lon is not None):
        mat_c, map_mm = climate_at_latlon(float(lat), float(lon))
        mult, dbg = climate_multiplier_from_mat_map(mat_c, map_mm)

        # scale yearly and cumulative
        out["CO2_tons"] *= mult
        out["CO2_cumulative_tons"] *= mult

        # stash climate info
        out.attrs["climate_info"] = dbg

    return out, None


def compute_multi(species_list, years: int, trees: int):
    results = []
    for sp in species_list:
        df, err = compute_curve(sp, years, trees)  # dashboard has no lat/lon
        if err:
            return None, err
        results.append(df)
    return results, None

# ---------- Plot helpers ----------
def plot_matplotlib_overlay(dfs, years, trees):
    """Return base64 PNG overlay of yearly bars (stacked) + lines for cumulative per species."""
    fig = plt.figure(figsize=(9.5, 5.2), dpi=130)
    ax = plt.gca()

    ages = dfs[0]["age_years"].values
    stacked_yearly = np.zeros_like(ages, dtype=float)
    for df in dfs:
        stacked_yearly += df["CO2_tons"].values
    ax.bar(ages, stacked_yearly, alpha=0.25, label="Total yearly CO₂ (t)")

    for df in dfs:
        ax.plot(df["age_years"], df["CO2_cumulative_tons"], marker="o", linewidth=2,
                label=f"{df['species'].iloc[0]} (cum)")

    title_species = ", ".join([df["species"].iloc[0] for df in dfs])
    ax.set_title(f"CO₂ Sequestration — {title_species} • {years} yrs • {trees} trees/species")
    ax.set_xlabel("Age (years)")
    ax.set_ylabel("CO₂ (tons)")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(ncol=2)
    fig.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("utf-8")


def make_plotly_json(dfs):
    """Return JSON serializable figure for interactive chart."""
    traces = []
    ages = dfs[0]["age_years"].tolist()
    stacked = np.sum([df["CO2_tons"].values for df in dfs], axis=0).tolist()
    traces.append(go.Bar(x=ages, y=stacked, name="Total yearly CO₂ (t)", opacity=0.35))

    for df in dfs:
        traces.append(go.Scatter(
            x=df["age_years"].tolist(),
            y=df["CO2_cumulative_tons"].tolist(),
            mode="lines+markers",
            name=f"{df['species'].iloc[0]} (cum)"
        ))

    layout = go.Layout(
        title="Interactive CO₂ Sequestration",
        xaxis=dict(title="Age (years)"),
        yaxis=dict(title="CO₂ (tons)"),
        hovermode="x unified",
        legend=dict(orientation="h")
    )
    fig = go.Figure(data=traces, layout=layout)
    return json.loads(fig.to_json())

# ---- Climate response curve (documented, not dummy) ----
def climate_multiplier_from_mat_map(mat_c, map_mm):
    """
    mat_c: mean annual temperature in °C
    map_mm: mean annual precipitation in mm
    Returns a scalar multiplier ~[0.5, 1.6]
    """
    if mat_c is None or map_mm is None:
        return 1.0, {"mat_c": None, "map_mm": None, "temp_factor": None, "rain_factor": None, "multiplier": 1.0}

    # Temperature bell curve centered ~25C with wide tolerance
    temp_factor = math.exp(-((mat_c - 25.0) / 12.0) ** 2)

    # Rainfall saturating response; approaches ~1.2 in very wet climates
    rain_factor = (1.0 - math.exp(-map_mm / 900.0)) * 1.2

    mult = max(0.5, min(1.6, temp_factor * rain_factor))

    dbg = {
        "mat_c": round(mat_c, 2),
        "map_mm": round(map_mm, 0),
        "temp_factor": round(temp_factor, 3),
        "rain_factor": round(rain_factor, 3),
        "multiplier": round(mult, 3),
    }
    return mult, dbg

# ---------- Landing page ----------
@app.route("/")
def landing():
    return render_template("landing.html")

# ---------- Dashboard (moved to /app) ----------
@app.route("/app", methods=["GET", "POST"])
def app_page():
    years = int(request.form.get("years", 20))
    trees = int(request.form.get("trees", 100))

    sel_species = request.form.getlist("species")
    if not sel_species:
        sel_species = [SPECIES_LIST[0]] if SPECIES_LIST else []

    dfs, error = (None, None)
    plot_url = None
    plotly_fig = None
    table_rows = []

    try:
        if sel_species:
            dfs, error = compute_multi(sel_species, years, trees)
            if not error:
                plot_url = plot_matplotlib_overlay(dfs, years, trees)
                plotly_fig = make_plotly_json(dfs)
                for df in dfs:
                    last = df.iloc[-1]
                    table_rows.append({
                        "species": df["species"].iloc[0],
                        "age_years": int(last["age_years"]),
                        "trees_alive": int(round(last["trees_alive"])),
                        "co2_year_t": round(float(last["CO2_tons"]), 3),
                        "co2_cum_t": round(float(last["CO2_cumulative_tons"]), 3)
                    })
    except Exception as e:
        error = f"Unexpected error: {e}"
        traceback.print_exc()

    csv_url = url_for("export_csv") + "?" + "&".join([f"species={s}" for s in sel_species]) + f"&years={years}&trees={trees}"
    pdf_url = url_for("export_pdf") + "?" + "&".join([f"species={s}" for s in sel_species]) + f"&years={years}&trees={trees}"

    return render_template(
        "index.html",
        species_list=SPECIES_LIST,
        selected_species=sel_species,
        years=years,
        trees=trees,
        error=error,
        plot_url=plot_url,
        plotly_fig=plotly_fig,
        table_rows=table_rows,
        csv_url=csv_url,
        pdf_url=pdf_url
    )

# ---------- Exports ----------
@app.route("/export/csv")
def export_csv():
    species = request.args.getlist("species")
    years = int(request.args.get("years", 20))
    trees = int(request.args.get("trees", 100))
    if not species:
        return Response("species required", status=400)

    dfs, err = compute_multi(species, years, trees)
    if err:
        return Response(err, status=400)

    out = pd.concat(dfs, ignore_index=True)
    buf = io.StringIO()
    out.to_csv(buf, index=False)
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=simulation.csv"}
    )


@app.route("/export/pdf")
def export_pdf():
    species = request.args.getlist("species")
    years = int(request.args.get("years", 20))
    trees = int(request.args.get("trees", 100))
    if not species:
        return Response("species required", status=400)

    dfs, err = compute_multi(species, years, trees)
    if err:
        return Response(err, status=400)

    img_b64 = plot_matplotlib_overlay(dfs, years, trees)
    img_bytes = base64.b64decode(img_b64.split(",", 1)[1])
    img_reader = ImageReader(io.BytesIO(img_bytes))

    pdf_buf = io.BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 50, "Afforestation Impact — Simulation Report")

    c.setFont("Helvetica", 10)
    c.drawString(40, height - 70, f"Species: {', '.join(species)}")
    c.drawString(40, height - 85, f"Years: {years}   Trees/species: {trees}")

    img_w, img_h = 520, 280
    c.drawImage(img_reader, 40, height - 90 - img_h, width=img_w, height=img_h)

    y = height - 100 - img_h
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Final-year stats")
    y -= 14
    c.setFont("Helvetica", 10)
    for df in dfs:
        last = df.iloc[-1]
        line = f"- {df['species'].iloc[0]}: Alive={int(round(last['trees_alive']))}, Yearly CO₂={last['CO2_tons']:.3f} t, Cumulative CO₂={last['CO2_cumulative_tons']:.3f} t"
        c.drawString(40, y, line)
        y -= 12

    c.showPage()
    c.save()
    pdf_buf.seek(0)

    return send_file(
        pdf_buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="simulation_report.pdf"
    )

# ---------- Map View (Folium in iframe; marker handled via JS) ----------
@app.route("/map", methods=["GET", "POST"])
def map_view():
    # Defaults; the form values carry the last chosen point
    lat = float(request.form.get("lat", 12.9716))
    lon = float(request.form.get("lon", 77.5946))
    years = int(request.form.get("years", 20))
    trees = int(request.form.get("trees", 100))
    species = request.form.get("species", SPECIES_LIST[0] if SPECIES_LIST else "")

    df, err = (None, None)
    stats = None
    try:
        if species:
            # pass lat/lon so climate scaling applies
            df, err = compute_curve(species, years, trees, lat=lat, lon=lon)
            if not err:
                last = df.iloc[-1]
                stats = {
                    "species": species,
                    "years": years,
                    "trees": trees,
                    "trees_alive": int(round(last["trees_alive"])),
                    "co2_year_t": round(float(last["CO2_tons"]), 3),
                    "co2_cum_t": round(float(last["CO2_cumulative_tons"]), 3),
                }
                clim = df.attrs.get("climate_info")
                if clim:
                    stats.update({
                        "mat_c": clim.get("mat_c"),
                        "map_mm": clim.get("map_mm"),
                        "temp_factor": clim.get("temp_factor"),
                        "rain_factor": clim.get("rain_factor"),
                        "climate_multiplier": clim.get("multiplier"),
                    })
    except Exception as e:
        err = f"Unexpected error: {e}"
        traceback.print_exc()

    # Build map (no server-side marker; JS inside iframe manages it)
    fmap = folium.Map(location=[lat, lon], zoom_start=10, tiles="CartoDB positron")
    map_name = fmap.get_name()
    map_html = fmap._repr_html_()

    return render_template(
        "map.html",
        species_list=SPECIES_LIST,
        species=species,
        years=years,
        trees=trees,
        lat=lat, lon=lon,
        error=err,
        stats=stats,
        map_html=map_html,
        map_name=map_name,
    )

@app.route("/health")
def health():
    ok = (DF_GROWTH is not None) and (DF_SPECIES is not None) and (len(SPECIES_LIST) > 0)
    return {"ok": ok, "species_count": len(SPECIES_LIST)}

if __name__ == "__main__":
    print("Template folder:", os.path.abspath(app.template_folder or "templates"))
    print("Static folder  :", os.path.abspath(app.static_folder or "static"))
    app.run(debug=True, port=5050)
