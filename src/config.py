# src/config.py
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

def pick_csv(base_name: str, vtag: str = "v2") -> str:
    """
    Return the path to the preferred CSV (…_v2.csv if present, else … .csv).
    Example: pick_csv("growth_curves_filled") → data/growth_curves_filled_v2.csv (if exists)
    """
    preferred = DATA_DIR / f"{base_name}_{vtag}.csv"
    fallback  = DATA_DIR / f"{base_name}.csv"
    return str(preferred if preferred.exists() else fallback)
