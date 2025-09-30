# src/climate.py
import os
import math
import numpy as np
import rasterio

# Expected paths (relative to project root)
WC_PATH_BIO1 = os.path.join("data", "worldclim", "bio", "wc2.1_10m_bio_1.tif")   # Annual mean temp (°C*10)
WC_PATH_BIO12 = os.path.join("data", "worldclim", "bio", "wc2.1_10m_bio_12.tif") # Annual precip (mm)

_bio1_ds = None
_bio12_ds = None

def _open_once():
    """
    Lazily open the WorldClim rasters and cache the dataset handles.
    Safe to call multiple times.
    """
    global _bio1_ds, _bio12_ds

    if _bio1_ds is None:
        if not os.path.exists(WC_PATH_BIO1):
            return
        try:
            _bio1_ds = rasterio.open(WC_PATH_BIO1)
        except Exception:
            _bio1_ds = None

    if _bio12_ds is None:
        if not os.path.exists(WC_PATH_BIO12):
            return
        try:
            _bio12_ds = rasterio.open(WC_PATH_BIO12)
        except Exception:
            _bio12_ds = None

def _is_valid_sample(val, nodata):
    """
    Returns True if a sampled raster value is valid (not nodata/masked/NaN).
    `val` may be a numpy scalar or a masked scalar.
    """
    # masked?
    if np.ma.isMaskedArray(val) or getattr(val, 'mask', False) is True:
        return False

    # unwrap numpy scalar
    v = float(val)

    # check nodata / NaN / inf
    if nodata is not None and v == float(nodata):
        return False
    if math.isnan(v) or math.isinf(v):
        return False

    return True

def climate_at_latlon(lat: float, lon: float):
    """
    Sample WorldClim v2.1 rasters at (lat, lon).

    Returns:
        (mat_c, map_mm)
        - mat_c: Mean Annual Temperature in °C (BIO1 is stored as °C*10)
        - map_mm: Mean Annual Precipitation in mm (BIO12)

    If rasters are missing or the sample is invalid, returns (None, None).
    """
    _open_once()
    if _bio1_ds is None or _bio12_ds is None:
        return None, None

    # WorldClim rasters are in WGS84 lon/lat; rasterio.sample expects (x, y) = (lon, lat)
    coords = [(float(lon), float(lat))]

    try:
        # Read one pixel value at the coordinate for each raster (band 1 by default)
        v1 = list(_bio1_ds.sample(coords))[0][0]
        v12 = list(_bio12_ds.sample(coords))[0][0]
    except Exception:
        return None, None

    # Validate samples against nodata/masked/NaN
    if not _is_valid_sample(v1, _bio1_ds.nodata):
        return None, None
    if not _is_valid_sample(v12, _bio12_ds.nodata):
        return None, None

    # Convert to Python floats
    v1 = float(v1)
    v12 = float(v12)

    # BIO1 is °C * 10 → convert to °C
    mat_c = v1 / 10.0
    map_mm = v12

    return mat_c, map_mm

def close_datasets():
    """
    Optional: close datasets if you need to reload or during shutdown.
    """
    global _bio1_ds, _bio12_ds
    try:
        if _bio1_ds is not None:
            _bio1_ds.close()
    finally:
        _bio1_ds = None

    try:
        if _bio12_ds is not None:
            _bio12_ds.close()
    finally:
        _bio12_ds = None
