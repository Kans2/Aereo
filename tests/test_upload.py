"""Tests for file upload validation."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.file_service import validate_file


class TestValidateFile:
    """File type validation."""

    def test_zip_is_shapefile(self):
        file = MagicMock()
        file.filename = "survey.zip"
        ext, ftype = validate_file(file)
        assert ext == ".zip"
        assert ftype == "shapefile"

    def test_kml_is_kml(self):
        file = MagicMock()
        file.filename = "survey.kml"
        ext, ftype = validate_file(file)
        assert ext == ".kml"
        assert ftype == "kml"

    def test_uppercase_extension_accepted(self):
        file = MagicMock()
        file.filename = "Survey.KML"
        ext, ftype = validate_file(file)
        assert ftype == "kml"

    def test_unsupported_format_raises(self):
        file = MagicMock()
        file.filename = "data.geojson"
        with pytest.raises(ValueError, match="Unsupported"):
            validate_file(file)

    def test_no_filename_raises(self):
        file = MagicMock()
        file.filename = None
        with pytest.raises(ValueError, match="Filename"):
            validate_file(file)

    def test_no_extension_raises(self):
        file = MagicMock()
        file.filename = "noextension"
        with pytest.raises(ValueError, match="Unsupported"):
            validate_file(file)
