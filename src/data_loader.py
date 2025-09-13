# src/data_loader.py

import pandas as pd

def load_growth_curves(filepath: str) -> pd.DataFrame:
    """Load tree growth curves dataset."""
    try:
        df = pd.read_csv(filepath)
        print(f"✅ Loaded growth curves with columns: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"❌ Failed to load growth curves: {e}")
        return pd.DataFrame()

def load_species_master(filepath: str) -> pd.DataFrame:
    """Load species master dataset and validate key columns."""
    try:
        df = pd.read_csv(filepath)
        print(f"✅ Loaded species master with columns: {list(df.columns)}")

        # Pick the correct species identifier column
        if "species" not in df.columns:
            if "species_scientific" in df.columns:
                df = df.rename(columns={"species_scientific": "species"})
                print("ℹ️ Renamed 'species_scientific' → 'species'")
            else:
                print("❌ No valid species column found (expected 'species' or 'species_scientific').")
        return df
    except Exception as e:
        print(f"❌ Failed to load species master: {e}")
        return pd.DataFrame()
