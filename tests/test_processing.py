"""Tests for the geo-processor service — file reading and processing."""

import os
import zipfile
import tempfile

import pytest
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, mapping
import fiona
from fiona.crs import from_epsg

from app.services.geo_processor import _read_kml, _read_shapefile


class TestReadKML:
    """KML file reading."""

    def test_reads_kml_features(self, sample_kml_file):
        gdf = _read_kml(sample_kml_file)
        assert gdf is not None
        assert len(gdf) == 3  # polygon, linestring, point

    def test_kml_has_geometry(self, sample_kml_file):
        gdf = _read_kml(sample_kml_file)
        assert gdf.geometry is not None
        geom_types = set(gdf.geometry.geom_type)
        assert "Polygon" in geom_types or "LineString" in geom_types or "Point" in geom_types


class TestReadShapefile:
    """Shapefile (ZIP) reading."""

    def test_reads_shapefile_from_zip(self, sample_shapefile_zip):
        gdf = _read_shapefile(sample_shapefile_zip)
        assert gdf is not None
        assert len(gdf) == 1

    def test_shapefile_has_polygon(self, sample_shapefile_zip):
        gdf = _read_shapefile(sample_shapefile_zip)
        assert gdf.geometry.iloc[0].geom_type == "Polygon"

    def test_shapefile_has_crs(self, sample_shapefile_zip):
        gdf = _read_shapefile(sample_shapefile_zip)
        assert gdf.crs is not None

    def test_invalid_zip_raises(self, tmp_path):
        """A ZIP with no .shp inside should raise ValueError."""
        bad_zip = tmp_path / "bad.zip"
        with zipfile.ZipFile(str(bad_zip), "w") as zf:
            zf.writestr("readme.txt", "no shapefile here")
        with pytest.raises(ValueError, match="No .shp file"):
            _read_shapefile(str(bad_zip))
