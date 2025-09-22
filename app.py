from flask import Flask, request, jsonify, render_template_string
import sys
from src.data_loader import load_growth_curves, load_species_master
from src.model import biomass_to_co2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

HTML_FORM = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Afforestation Model</title>
    <style>
        body { font-family: Arial, sans-serif; background: #eafbe7; margin: 0; padding: 0; }
        .container { max-width: 500px; margin: 40px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #b2d8b2; padding: 32px; }
        h2 { color: #2e7d32; }
        label { display: block; margin-top: 16px; }
        select, input[type=number] { width: 100%; padding: 8px; margin-top: 4px; border-radius: 4px; border: 1px solid #b2d8b2; }
        button { margin-top: 24px; background: #43a047; color: #fff; border: none; padding: 12px 24px; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .result { margin-top: 32px; background: #e8f5e9; padding: 16px; border-radius: 6px; }
        .error { color: #c62828; margin-top: 24px; }
        .plot-img { margin-top: 24px; max-width: 100%; border-radius: 6px; box-shadow: 0 1px 4px #b2d8b2; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Afforestation CO₂ Sequestration Calculator</h2>
        <form method="POST">
            <label for="species">Tree Species:</label>
            <select name="species" id="species" required>
                {% for s in species_list %}
                <option value="{{s}}" {% if s==selected_species %}selected{% endif %}>{{s}}</option>
                {% endfor %}
            </select>
            <label for="years">Years:</label>
            <input type="number" name="years" id="years" min="1" max="100" value="{{years}}" required>
            <label for="trees">Number of Trees:</label>
            <input type="number" name="trees" id="trees" min="1" max="100000" value="{{trees}}" required>
            <button type="submit">Simulate</button>
        </form>
        {% if result %}
        <div class="result">
            <strong>Summary:</strong><br>
            {{result['summary']}}<br><br>
            <strong>Yearly CO₂ Sequestered:</strong>
            <ul>
            {% for r in result['results'] %}
                <li>Year {{r['age_years']}}: {{r['Total_CO2_sequestered']|round(2)}} kg</li>
            {% endfor %}
            </ul>
            {% if plot_url %}
            <img class="plot-img" src="{{plot_url}}" alt="CO₂ Sequestration Graph">
            {% endif %}
        </div>
        {% endif %}
        {% if error %}
        <div class="error">{{error}}</div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    df_species = load_species_master("data/species_master_filled.csv")
    species_col = None
    for col in df_species.columns:
        if col.lower() in ["species", "tree", "tree_species", "name"]:
            species_col = col
            break
    if not species_col:
        return render_template_string(HTML_FORM, species_list=[], error="Species column not found", result=None, selected_species=None, years=5, trees=100, plot_url=None)
    species_list = sorted(df_species[species_col].unique())
    error = None
    result = None
    plot_url = None
    selected_species = species_list[0] if species_list else None
    years = 5
    trees = 100
    if request.method == 'POST':
        selected_species = request.form.get('species')
        years = int(request.form.get('years', 5))
        trees = int(request.form.get('trees', 100))
        df_growth = load_growth_curves("data/growth_curves_filled.csv")
        if selected_species not in df_species[species_col].values:
            error = f"Species '{selected_species}' not found"
        else:
            # Filter growth data
            if "species_scientific" in df_growth.columns:
                growth_col = "species_scientific"
            else:
                growth_col = df_growth.columns[0]
            species_growth = df_growth[df_growth[growth_col] == selected_species]
            species_growth = species_growth[species_growth["age_years"] <= years].copy()
            if species_growth.empty:
                error = f"No growth data for {selected_species} up to {years} years"
            else:
                # Compute CO2
                if "Biomass_kg" in species_growth.columns:
                    species_growth["CO2_sequestered_per_tree"] = species_growth["Biomass_kg"].apply(biomass_to_co2)
                    species_growth["Total_CO2_sequestered"] = species_growth["CO2_sequestered_per_tree"] * trees
                elif "dbh_cm" in species_growth.columns and "height_m" in species_growth.columns:
                    wood_density_col = None
                    for col in df_species.columns:
                        if col.lower() in ["wood_density_g_cm3", "wood_density", "density"]:
                            wood_density_col = col
                            break
                    if not wood_density_col:
                        error = 'Wood density column not found'
                    else:
                        wood_density = df_species.loc[df_species[species_col] == selected_species, wood_density_col].values
                        if len(wood_density) == 0:
                            error = f"Wood density not found for {selected_species}"
                        else:
                            wood_density = float(wood_density[0])
                            species_growth["Biomass_kg"] = 0.0673 * (wood_density * species_growth["dbh_cm"]**2 * species_growth["height_m"])**0.976
                            species_growth["CO2_sequestered_per_tree"] = species_growth["Biomass_kg"].apply(biomass_to_co2)
                            species_growth["Total_CO2_sequestered"] = species_growth["CO2_sequestered_per_tree"] * trees
                else:
                    error = 'Insufficient data to compute biomass'
                if not error:
                    results = species_growth[["age_years", "Total_CO2_sequestered"]].to_dict(orient="records")
                    final_val = species_growth["Total_CO2_sequestered"].iloc[-1] / 1000
                    result = {
                        'results': results,
                        'summary': f"Planting {trees} {selected_species} trees will sequester ~{final_val:.2f} metric tons of CO₂ over {years} years."
                    }
                    # Generate plot in memory
                    fig, ax = plt.subplots(figsize=(6,4))
                    ax.plot([r['age_years'] for r in results], [r['Total_CO2_sequestered'] for r in results], marker='o', color='#388e3c')
                    ax.set_xlabel('Year')
                    ax.set_ylabel('Total CO₂ Sequestered (kg)')
                    ax.set_title('Yearly CO₂ Sequestration')
                    ax.grid(True, linestyle='--', alpha=0.5)
                    fig.tight_layout()
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png')
                    plt.close(fig)
                    buf.seek(0)
                    plot_data = base64.b64encode(buf.read()).decode('utf-8')
                    plot_url = f'data:image/png;base64,{plot_data}'
    return render_template_string(HTML_FORM, species_list=species_list, error=error, result=result, selected_species=selected_species, years=years, trees=trees, plot_url=plot_url)

if __name__ == "__main__":
    app.run(debug=True, port=5050)
