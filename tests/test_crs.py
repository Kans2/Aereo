"""Unit tests for CRS handling."""

import pytest
from shapely.geometry import Point, Polygon

from app.services.crs_handler import (
    get_projected_crs,
    get_utm_epsg,
    transform_geometry,
)


class TestUTMZoneDetection:
    """Auto UTM zone selection based on coordinates."""

    def test_northern_hemisphere(self):
        # Bangalore, India → UTM zone 43N
        assert get_utm_epsg(77.5946, 12.9716) == "EPSG:32643"

    def test_southern_hemisphere(self):
        # Sydney, Australia → UTM zone 56S
        assert get_utm_epsg(151.2093, -33.8688) == "EPSG:32756"

    def test_prime_meridian(self):
        # London → UTM zone 30N
        assert get_utm_epsg(-0.1276, 51.5074) == "EPSG:32630"

    def test_date_line_east(self):
        # Fiji → UTM zone 60S
        assert get_utm_epsg(179.0, -17.7) == "EPSG:32760"

    def test_date_line_west(self):
        # Near date line, western side → UTM zone 1N
        assert get_utm_epsg(-179.5, 10.0) == "EPSG:32601"


class TestProjectedCRS:
    """get_projected_crs returns the source when already projected."""

    def test_geographic_crs_returns_utm(self):
        geom = Point(77.5946, 12.9716)
        result = get_projected_crs(geom, "EPSG:4326")
        assert result.startswith("EPSG:326")  # northern UTM

    def test_projected_crs_returns_self(self):
        geom = Point(500000, 1500000)
        result = get_projected_crs(geom, "EPSG:32643")
        assert result == "EPSG:32643"


class TestTransformGeometry:
    """Geometry reprojection between CRS."""

    def test_transform_changes_coords(self):
        geom = Point(77.5946, 12.9716)
        transformed = transform_geometry(geom, "EPSG:4326", "EPSG:32643")
        # UTM coordinates are in metres, so x should be ~hundreds of thousands
        assert transformed.x > 100_000
        assert transformed.y > 100_000

    def test_same_crs_returns_identical(self):
        geom = Point(500000, 1500000)
        result = transform_geometry(geom, "EPSG:32643", "EPSG:32643")
        assert abs(result.x - geom.x) < 1e-6
        assert abs(result.y - geom.y) < 1e-6

    def test_polygon_transform(self):
        poly = Polygon(
            [
                (77.5946, 12.9716),
                (77.5946, 12.9816),
                (77.6046, 12.9816),
                (77.6046, 12.9716),
                (77.5946, 12.9716),
            ]
        )
        transformed = transform_geometry(poly, "EPSG:4326", "EPSG:32643")
        # Polygon area should be > 0 in projected coords (metres²)
        assert transformed.area > 0
