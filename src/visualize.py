import matplotlib.pyplot as plt

def plot_co2(species_growth, species, trees):
    years = species_growth["age_years"]
    total_co2 = species_growth["Total_CO2_sequestered"] / 1000  # tons

    plt.figure(figsize=(8,5))
    plt.plot(years, total_co2, marker="o", linestyle="-", color="green")

    plt.title(f"CO₂ Sequestration for {trees} {species} Trees")
    plt.xlabel("Years")
    plt.ylabel("CO₂ Sequestered (tons)")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.show()
