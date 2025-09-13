import matplotlib.pyplot as plt
from src.data_loader import load_growth_curves
from src.model import biomass_to_co2

def compare_species(species_list, years, trees):
    df_growth = load_growth_curves("data/growth_curves_filled.csv")

    if "species_scientific" in df_growth.columns:
        growth_col = "species_scientific"
    else:
        growth_col = df_growth.columns[0]

    plt.figure(figsize=(8,5))

    for species in species_list:
        species_growth = df_growth[df_growth[growth_col] == species]
        species_growth = species_growth[species_growth["age_years"] <= years].copy()

        if species_growth.empty:
            print(f"⚠️ No data for {species}, skipping...")
            continue

        if "Biomass_kg" in species_growth.columns:
            species_growth["CO2_total"] = species_growth["Biomass_kg"].apply(biomass_to_co2) * trees
            plt.plot(
                species_growth["age_years"],
                species_growth["CO2_total"]/1000,   # tons
                marker="o",
                label=species
            )
        else:
            print(f"❌ No Biomass_kg column for {species}, skipping...")

    plt.title(f"CO₂ Sequestration Comparison ({trees} trees)")
    plt.xlabel("Years")
    plt.ylabel("CO₂ Sequestered (tons)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.show()
