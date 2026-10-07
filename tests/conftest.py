"""Shared test fixtures and configuration."""

import os
import tempfile
import json
import zipfile

import pytest
from shapely.geometry import Point, LineString, Polygon, mapping
import fiona
from fiona.crs import from_epsg


@pytest.fixture()
def tmp_upload_dir(tmp_path):
    """Provide a temporary upload directory."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return str(upload_dir)


@pytest.fixture()
def sample_kml_file(tmp_path):
    """Create a sample KML file with a polygon, a linestring, and a point."""
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Test KML</name>
    <Placemark>
      <name>Test Polygon</name>
      <description>A sample polygon</description>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              77.5946,12.9716,0
              77.5946,12.9816,0
              77.6046,12.9816,0
              77.6046,12.9716,0
              77.5946,12.9716,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
    <Placemark>
      <name>Test Line</name>
      <description>A sample linestring</description>
      <LineString>
        <coordinates>
          77.5946,12.9716,0
          77.6046,12.9816,0
        </coordinates>
      </LineString>
    </Placemark>
    <Placemark>
      <name>Test Point</name>
      <description>A sample point</description>
      <Point>
        <coordinates>77.5946,12.9716,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>"""
    kml_path = tmp_path / "test.kml"
    kml_path.write_text(kml_content, encoding="utf-8")
    return str(kml_path)


@pytest.fixture()
def sample_shapefile_zip(tmp_path):
    """Create a sample shapefile (zipped) with a polygon feature."""
    shp_dir = tmp_path / "shp_data"
    shp_dir.mkdir()
    shp_path = str(shp_dir / "test.shp")

    schema = {
        "geometry": "Polygon",
        "properties": {"name": "str", "value": "float"},
    }

    with fiona.open(
        shp_path,
        "w",
        driver="ESRI Shapefile",
        schema=schema,
        crs=from_epsg(4326),
    ) as dst:
        dst.write(
            {
                "geometry": mapping(
                    Polygon(
                        [
                            (77.5946, 12.9716),
                            (77.5946, 12.9816),
                            (77.6046, 12.9816),
                            (77.6046, 12.9716),
                            (77.5946, 12.9716),
                        ]
                    )
                ),
                "properties": {"name": "Zone A", "value": 42.5},
            }
        )

    # Zip all shapefile components
    zip_path = tmp_path / "test_shapefile.zip"
    with zipfile.ZipFile(str(zip_path), "w") as zf:
        for f in shp_dir.iterdir():
            zf.write(str(f), f.name)

    return str(zip_path)
