"""
Measurement calculator for geospatial geometries.

Supported geometry types and their measurements:
─────────────────────────────────────────────────
  Polygon / MultiPolygon       → Area  (m²)
  LineString / MultiLineString → Length (m)
  Point / MultiPoint           → No measurement (gracefully skipped)
  GeometryCollection           → Per-component (summed)
  Other                        → Gracefully skipped
"""

import logging
from typing import Optional, Tuple

from shapely.geometry.base import BaseGeometry

logger = logging.getLogger(__name__)

POLYGON_TYPES = frozenset({"Polygon", "MultiPolygon"})
LINE_TYPES = frozenset({"LineString", "MultiLineString"})
POINT_TYPES = frozenset({"Point", "MultiPoint"})

# Type alias for the measurement result tuple
MeasurementResult = Tuple[Optional[float], Optional[float], bool, Optional[str]]


def calculate_measurement(geometry: BaseGeometry, geometry_type: str) -> MeasurementResult:
    """Calculate measurements for *geometry* based on its type.

    Parameters
    ----------
    geometry : BaseGeometry
        A Shapely geometry **already projected** to a metre-based CRS.
    geometry_type : str
        The OGC geometry type name (e.g. "Polygon", "LineString").

    Returns
    -------
    tuple
        ``(area_sq_meters, length_meters, measurement_supported, note)``
    """
    if geometry is None or geometry.is_empty:
        return (None, None, False, "Empty or null geometry")

    if geometry_type in POLYGON_TYPES:
        area = round(geometry.area, 4)
        return (area, None, True, None)

    if geometry_type in LINE_TYPES:
        length = round(geometry.length, 4)
        return (None, length, True, None)

    if geometry_type in POINT_TYPES:
        return (None, None, False, f"No measurement required for {geometry_type} geometry")

    if geometry_type == "GeometryCollection":
        return _measure_geometry_collection(geometry)

    return (None, None, False, f"Unsupported geometry type: {geometry_type}")


def _measure_geometry_collection(geometry: BaseGeometry) -> MeasurementResult:
    """Sum areas and lengths across the sub-geometries of a collection."""
    total_area = 0.0
    total_length = 0.0
    has_polygon = False
    has_line = False

    for geom in geometry.geoms:
        gt = geom.geom_type
        if gt in POLYGON_TYPES:
            total_area += geom.area
            has_polygon = True
        elif gt in LINE_TYPES:
            total_length += geom.length
            has_line = True
        # Points and other types are silently skipped

    area = round(total_area, 4) if has_polygon else None
    length = round(total_length, 4) if has_line else None
    supported = has_polygon or has_line
    note = None if supported else "GeometryCollection contains no measurable geometries"

    return (area, length, supported, note)
