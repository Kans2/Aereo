"""Unit tests for the measurement calculator."""

import pytest
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from app.services.measurement import calculate_measurement


class TestPolygonMeasurement:
    """Polygon and MultiPolygon → area."""

    def test_polygon_returns_area(self):
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
        area, length, supported, note = calculate_measurement(poly, "Polygon")
        assert supported is True
        assert area == 100.0
        assert length is None
        assert note is None

    def test_multipolygon_returns_area(self):
        mp = MultiPolygon(
            [
                Polygon([(0, 0), (5, 0), (5, 5), (0, 5)]),
                Polygon([(10, 10), (15, 10), (15, 15), (10, 15)]),
            ]
        )
        area, length, supported, note = calculate_measurement(mp, "MultiPolygon")
        assert supported is True
        assert area == 50.0
        assert length is None


class TestLineStringMeasurement:
    """LineString and MultiLineString → length."""

    def test_linestring_returns_length(self):
        line = LineString([(0, 0), (3, 4)])
        area, length, supported, note = calculate_measurement(line, "LineString")
        assert supported is True
        assert length == 5.0
        assert area is None

    def test_multilinestring_returns_length(self):
        ml = MultiLineString([[(0, 0), (3, 4)], [(10, 0), (13, 4)]])
        area, length, supported, note = calculate_measurement(ml, "MultiLineString")
        assert supported is True
        assert length == 10.0


class TestPointMeasurement:
    """Point and MultiPoint → no measurement."""

    def test_point_not_supported(self):
        pt = Point(1, 2)
        area, length, supported, note = calculate_measurement(pt, "Point")
        assert supported is False
        assert area is None
        assert length is None
        assert "Point" in note

    def test_multipoint_not_supported(self):
        mp = MultiPoint([(0, 0), (1, 1)])
        area, length, supported, note = calculate_measurement(mp, "MultiPoint")
        assert supported is False


class TestGeometryCollection:
    """GeometryCollection → per-component sum."""

    def test_mixed_collection(self):
        gc = GeometryCollection(
            [
                Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]),
                LineString([(0, 0), (3, 4)]),
                Point(5, 5),
            ]
        )
        area, length, supported, note = calculate_measurement(
            gc, "GeometryCollection"
        )
        assert supported is True
        assert area == 100.0
        assert length == 5.0

    def test_points_only_collection(self):
        gc = GeometryCollection([Point(0, 0), Point(1, 1)])
        area, length, supported, note = calculate_measurement(
            gc, "GeometryCollection"
        )
        assert supported is False
        assert "no measurable" in note.lower()


class TestEdgeCases:
    """Empty / null geometry handling."""

    def test_empty_geometry(self):
        empty = Point()
        area, length, supported, note = calculate_measurement(empty, "Point")
        assert supported is False

    def test_unsupported_type(self):
        pt = Point(1, 2)
        area, length, supported, note = calculate_measurement(pt, "Unknown")
        assert supported is False
        assert "Unsupported" in note
