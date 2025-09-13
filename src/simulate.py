import matplotlib.pyplot as plt
from src.data_loader import load_growth_curves, load_species_master
from src.model import biomass_to_co2

def compare_species(species_list, years, trees):
    df_growth = load_growth_curves("data/growth_curves_filled.csv")
    df_species = load_species_master("data/species_master_filled.csv")

    if "species_scientific" in df_growth.columns:
        growth_col = "species_scientific"
    else:
        growth_col = df_growth.columns[0]

    # Find wood density column
    wood_density_col = None
    for col in df_species.columns:
        if col.lower() in ["wood_density_g_cm3", "wood_density", "density"]:
            wood_density_col = col
            break

    plt.figure(figsize=(8,5))

    for species in species_list:
        species_growth = df_growth[df_growth[growth_col] == species]
        species_growth = species_growth[species_growth["age_years"] <= years].copy()

        if species_growth.empty:
            print(f"⚠️ No data for {species}, skipping...")
            continue

        # Get wood density for the selected species
        wood_density = None
        if wood_density_col:
            wd_vals = df_species.loc[df_species["species"] == species, wood_density_col].values
            if len(wd_vals) > 0:
                wood_density = float(wd_vals[0])

        # Compute biomass if needed
        if "Biomass_kg" in species_growth.columns:
            species_growth["CO2_total"] = species_growth["Biomass_kg"].apply(biomass_to_co2) * trees
        elif ("dbh_cm" in species_growth.columns and "height_m" in species_growth.columns and wood_density):
            species_growth["Biomass_kg"] = 0.0673 * (wood_density * species_growth["dbh_cm"]**2 * species_growth["height_m"])**0.976
            species_growth["CO2_total"] = species_growth["Biomass_kg"].apply(biomass_to_co2) * trees
        else:
            print(f"❌ Insufficient data to compute biomass for {species}, skipping...")
            continue

        plt.plot(
            species_growth["age_years"],
            species_growth["CO2_total"]/1000,   # tons
            marker="o",
            label=species
        )

    plt.title(f"CO₂ Sequestration Comparison ({trees} trees)")
    plt.xlabel("Years")
    plt.ylabel("CO₂ Sequestered (tons)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.show()
