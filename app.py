from flask import Flask, request, jsonify
import sys
from flask_cors import CORS
from src.data_loader import load_growth_curves, load_species_master
from src.model import biomass_to_co2

app = Flask(__name__)
CORS(app)

@app.route('/api/species', methods=['GET'])
def get_species():
    df_species = load_species_master("data/species_master_filled.csv")
    species_col = None
    for col in df_species.columns:
        if col.lower() in ["species", "tree", "tree_species", "name"]:
            species_col = col
            break
    if not species_col:
        return jsonify({'error': 'Species column not found'}), 400
    species_list = sorted(df_species[species_col].unique())
    return jsonify({'species': species_list})

@app.route('/api/simulate', methods=['POST'])
def simulate():
    data = request.json
    species = data.get('species')
    years = int(data.get('years'))
    trees = int(data.get('trees'))

    df_growth = load_growth_curves("data/growth_curves_filled.csv")
    df_species = load_species_master("data/species_master_filled.csv")

    # Find species column
    species_col = None
    for col in df_species.columns:
        if col.lower() in ["species", "tree", "tree_species", "name"]:
            species_col = col
            break
    if not species_col:
        return jsonify({'error': 'Species column not found'}), 400
    if species not in df_species[species_col].values:
        return jsonify({'error': f"Species '{species}' not found"}), 400

    # Filter growth data
    if "species_scientific" in df_growth.columns:
        growth_col = "species_scientific"
    else:
        growth_col = df_growth.columns[0]
    species_growth = df_growth[df_growth[growth_col] == species]
    species_growth = species_growth[species_growth["age_years"] <= years].copy()
    if species_growth.empty:
        return jsonify({'error': f"No growth data for {species} up to {years} years"}), 400

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
            return jsonify({'error': 'Wood density column not found'}), 400
        wood_density = df_species.loc[df_species[species_col] == species, wood_density_col].values
        if len(wood_density) == 0:
            return jsonify({'error': f"Wood density not found for {species}"}), 400
        wood_density = float(wood_density[0])
        species_growth["Biomass_kg"] = 0.0673 * (wood_density * species_growth["dbh_cm"]**2 * species_growth["height_m"])**0.976
        species_growth["CO2_sequestered_per_tree"] = species_growth["Biomass_kg"].apply(biomass_to_co2)
        species_growth["Total_CO2_sequestered"] = species_growth["CO2_sequestered_per_tree"] * trees
    else:
        return jsonify({'error': 'Insufficient data to compute biomass'}), 400

    # Prepare results
    results = species_growth[["age_years", "Total_CO2_sequestered"]].to_dict(orient="records")
    final_val = species_growth["Total_CO2_sequestered"].iloc[-1] / 1000
    return jsonify({
        'results': results,
        'summary': f"Planting {trees} {species} trees will sequester ~{final_val:.2f} metric tons of CO₂ over {years} years."
    })

if __name__ == "__main__":
    app.run(debug=True, port=5050)
