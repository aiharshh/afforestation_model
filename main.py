import sys
from src.data_loader import load_growth_curves, load_species_master
from src.model import biomass_to_co2
from src.visualize import plot_co2

def main():
    # --- Load datasets ---
    df_growth = load_growth_curves("data/growth_curves_filled.csv")
    df_species = load_species_master("data/species_master_filled.csv")

    # --- Debug: print available columns ---
    print("\n✅ Loaded species master with columns:", list(df_species.columns))

    # Adjust column name if needed (make it flexible)
    species_col = None
    for col in df_species.columns:
        if col.lower() in ["species", "tree", "tree_species", "name"]:
            species_col = col
            break

    if not species_col:
        print("❌ Could not find a species column in species_master_filled.csv")
        sys.exit(1)

    print("\n🌱 Afforestation Impact Modeling 🌱\n")
    print("Available species:")
    for s in df_species[species_col].unique():
        print(f" - {s}")

    # --- Get user input ---
    species = input("\nEnter species name: ").strip()
    if species not in df_species[species_col].values:
        print(f"❌ Species '{species}' not found in dataset.")
        sys.exit(1)

    try:
        years = int(input("Enter simulation years (e.g., 20): ").strip())
        trees = int(input("Enter number of trees planted: ").strip())
    except ValueError:
        print("❌ Invalid input. Please enter numbers for years and trees.")
        sys.exit(1)

    # --- Filter growth data ---
    if "species_scientific" in df_growth.columns:
        growth_col = "species_scientific"
    else:
        growth_col = df_growth.columns[0]  # fallback to first column

    species_growth = df_growth[df_growth[growth_col] == species]
    species_growth = species_growth[species_growth["age_years"] <= years].copy()

    if species_growth.empty:
        print(f"⚠️ No growth data available for {species} up to {years} years.")
        sys.exit(1)

    # --- Compute CO₂ ---
    # If biomass column exists, use it; else, calculate from dbh_cm, height_m, and wood density
    if "Biomass_kg" in species_growth.columns:
        species_growth["CO2_sequestered_per_tree"] = species_growth["Biomass_kg"].apply(biomass_to_co2)
        species_growth["Total_CO2_sequestered"] = species_growth["CO2_sequestered_per_tree"] * trees
    elif "dbh_cm" in species_growth.columns and "height_m" in species_growth.columns:
        # Get wood density for the selected species from species master
        wood_density_col = None
        for col in df_species.columns:
            if col.lower() in ["wood_density_g_cm3", "wood_density", "density"]:
                wood_density_col = col
                break
        if not wood_density_col:
            print("❌ Wood density column not found in species master.")
            sys.exit(1)
        wood_density = df_species.loc[df_species[species_col] == species, wood_density_col].values
        if len(wood_density) == 0:
            print(f"❌ Wood density not found for species '{species}'.")
            sys.exit(1)
        wood_density = float(wood_density[0])
        # Calculate biomass using Chave et al. 2014 formula
        species_growth["Biomass_kg"] = 0.0673 * (wood_density * species_growth["dbh_cm"]**2 * species_growth["height_m"])**0.976
        species_growth["CO2_sequestered_per_tree"] = species_growth["Biomass_kg"].apply(biomass_to_co2)
        species_growth["Total_CO2_sequestered"] = species_growth["CO2_sequestered_per_tree"] * trees
    else:
        print("❌ Insufficient data to compute biomass. Please add dbh_cm and height_m columns.")
        sys.exit(1)

    # --- Results ---
    print("\n📊 Results (CO₂ in kg):")
    if "age_years" in species_growth.columns:
        print(species_growth[["age_years", "Total_CO2_sequestered"]])
    else:
        print(species_growth[[species_growth.columns[0], "Total_CO2_sequestered"]])

    final_val = species_growth["Total_CO2_sequestered"].iloc[-1] / 1000
    print(f"\n✅ Planting {trees} {species} trees will sequester ~{final_val:.2f} metric tons of CO₂ over {years} years.\n")

    # --- Plot ---
    plot_co2(species_growth, species, trees)

    # --- Multi-scenario comparison ---
    choice = input("\nDo you want to compare multiple species? (y/n): ").strip().lower()
    if choice == "y":
        species_list = input("Enter species names separated by commas: ").split(",")
        species_list = [s.strip() for s in species_list]
        from src.simulate import compare_species
        compare_species(species_list, years, trees)

if __name__ == "__main__":
    main()
