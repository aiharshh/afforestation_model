# src/data_loader.py
import pandas as pd
from .config import pick_csv

def load_growth_curves(path: str | None = None) -> pd.DataFrame:
    fp = path or pick_csv("growth_curves_filled")
    df = pd.read_csv(fp)
    # Ensure expected columns exist
    needed = {"species_scientific", "age_years", "dbh_cm", "height_m"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Growth curves missing columns: {missing} in {fp}")
    return df

def load_species_master(path: str | None = None) -> pd.DataFrame:
    fp = path or pick_csv("species_master_filled")
    df = pd.read_csv(fp)

    # Normalize species column name
    if "species" not in df.columns:
        if "species_scientific" in df.columns:
            df = df.rename(columns={"species_scientific": "species"})
        else:
            raise ValueError("No species column (species or species_scientific) found in species master.")

    # Fill defaults if not present
    if "carbon_fraction_CF" not in df.columns:
        df["carbon_fraction_CF"] = 0.47
    if "root_to_shoot_ratio_R" not in df.columns:
        df["root_to_shoot_ratio_R"] = 0.27
    if "annual_survival_rate" not in df.columns:
        df["annual_survival_rate"] = 0.95

    # Wood density
    wd_col = None
    for c in df.columns:
        if c.lower() in ("wood_density_g_cm3","wood_density","density","rho","ρ","rho_g_cm3"):
            wd_col = c
            break
    if wd_col is None:
        raise ValueError("No wood density column found in species master.")
    df = df.rename(columns={wd_col: "wood_density_g_cm3"})

    return df

def load_sim_results(path: str | None = None) -> pd.DataFrame:
    fp = path or pick_csv("sim_results")
    return pd.read_csv(fp)
