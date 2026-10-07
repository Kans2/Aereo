"""
CRS (Coordinate Reference System) handling.

Strategy: Auto UTM Zone Detection
──────────────────────────────────
1. Detect the source CRS from the uploaded file.
2. If the CRS is geographic (e.g. EPSG:4326), compute the centroid of
   the geometry and auto-select the matching UTM zone.
3. Transform the geometry to the projected CRS before calculating
   area / length, so results are in metres — not degrees.
"""

import logging
import math
from typing import Optional

from pyproj import CRS, Transformer
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform as shapely_transform

logger = logging.getLogger(__name__)


# ── UTM zone helpers ─────────────────────────────────────────────────────────


def get_utm_epsg(lon: float, lat: float) -> str:
    """Return the EPSG code for the UTM zone that covers *lon*/*lat*.

    Northern hemisphere → EPSG:326xx
    Southern hemisphere → EPSG:327xx
    """
    zone_number = int(math.floor((lon + 180) / 6)) + 1
    # Clamp to valid range [1, 60]
    zone_number = max(1, min(60, zone_number))

    if lat >= 0:
        return f"EPSG:{32600 + zone_number}"
    return f"EPSG:{32700 + zone_number}"


# ── CRS detection ────────────────────────────────────────────────────────────


def detect_crs_string(crs_obj) -> Optional[str]:
    """Convert a Fiona/GeoPandas CRS object to a human-readable EPSG string.

    Returns ``None`` when the CRS cannot be determined.
    """
    if crs_obj is None:
        return None
    try:
        crs = CRS.from_user_input(crs_obj)
        epsg = crs.to_epsg()
        if epsg:
            return f"EPSG:{epsg}"
        return crs.to_wkt()
    except Exception:
        return str(crs_obj)


# ── Projection helpers ───────────────────────────────────────────────────────


def get_projected_crs(geometry: BaseGeometry, source_crs: str) -> str:
    """Choose the best projected CRS for *geometry*.

    If the source is already projected (units = metres), it is returned as-is.
    Otherwise, a UTM zone is selected based on the geometry's centroid.
    """
    try:
        crs = CRS.from_user_input(source_crs)
        if crs.is_projected:
            return source_crs
    except Exception:
        logger.warning("Could not parse source CRS '%s'; assuming geographic.", source_crs)

    centroid = geometry.centroid
    return get_utm_epsg(centroid.x, centroid.y)


def transform_geometry(
    geometry: BaseGeometry,
    source_crs: str,
    target_crs: str,
) -> BaseGeometry:
    """Reproject *geometry* from *source_crs* to *target_crs*."""
    src = CRS.from_user_input(source_crs)
    dst = CRS.from_user_input(target_crs)

    if src == dst:
        return geometry

    transformer = Transformer.from_crs(src, dst, always_xy=True)
    return shapely_transform(transformer.transform, geometry)
