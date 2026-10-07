"""
Geospatial file processor.

Reads Shapefiles (.zip) and KML files, extracts features, transforms
geometries to a projected CRS, calculates measurements, and persists
everything to the database.
"""

import logging
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import fiona
import geopandas as gpd
from sqlalchemy.orm import Session

from app.models.feature import Feature
from app.models.file import FileStatus, GeoFile
from app.services.crs_handler import (
    detect_crs_string,
    get_projected_crs,
    transform_geometry,
)
from app.services.measurement import calculate_measurement

logger = logging.getLogger(__name__)


# ── Public entry point ───────────────────────────────────────────────────────


def process_file(db: Session, file_id: str, file_path: str, file_type: str) -> None:
    """Background task: parse a geospatial file and store measurements.

    This function is designed to run in a background thread (via FastAPI
    ``BackgroundTasks``).  It manages its own commits so the caller does
    not need to handle the session.
    """
    try:
        # ── mark PROCESSING ──────────────────────────────────────────
        geo_file = db.query(GeoFile).filter(GeoFile.id == file_id).first()
        if geo_file is None:
            logger.error("File record %s not found — aborting", file_id)
            return

        geo_file.status = FileStatus.PROCESSING
        db.commit()

        # ── read the geospatial file ─────────────────────────────────
        gdf = _read_file(file_path, file_type)

        if gdf is None or gdf.empty:
            _mark_failed(db, geo_file, "No features found in the uploaded file")
            return

        # ── detect source CRS ────────────────────────────────────────
        source_crs = detect_crs_string(gdf.crs) or "EPSG:4326"
        if gdf.crs is None:
            logger.warning(
                "File %s has no CRS metadata — assuming EPSG:4326", file_id
            )
        geo_file.original_crs = source_crs

        # ── iterate features ─────────────────────────────────────────
        features: list[Feature] = []
        for idx, row in gdf.iterrows():
            geometry = row.geometry
            if geometry is None or geometry.is_empty:
                continue

            geometry_type = geometry.geom_type
            properties = _extract_properties(row, gdf)

            # project → measure
            try:
                projected_crs = get_projected_crs(geometry, source_crs)
                projected_geom = transform_geometry(geometry, source_crs, projected_crs)
            except Exception as exc:
                logger.warning(
                    "CRS transform failed for feature %s: %s", idx, exc
                )
                projected_geom = geometry
                projected_crs = source_crs

            area, length, supported, note = calculate_measurement(
                projected_geom, geometry_type
            )

            features.append(
                Feature(
                    file_id=file_id,
                    feature_index=idx if isinstance(idx, int) else len(features),
                    geometry_type=geometry_type,
                    geometry_wkt=geometry.wkt,
                    original_crs=source_crs,
                    projected_crs=projected_crs,
                    properties=properties,
                    area_sq_meters=area,
                    length_meters=length,
                    measurement_supported=supported,
                    measurement_note=note,
                )
            )

        # ── persist ──────────────────────────────────────────────────
        db.add_all(features)
        geo_file.feature_count = len(features)
        geo_file.status = FileStatus.COMPLETED
        geo_file.processed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            "Processed file %s — %d features extracted", file_id, len(features)
        )

    except Exception as exc:
        logger.error("Error processing file %s: %s", file_id, exc, exc_info=True)
        try:
            geo_file = db.query(GeoFile).filter(GeoFile.id == file_id).first()
            if geo_file:
                _mark_failed(db, geo_file, str(exc))
        except Exception as db_err:
            logger.error("Could not update status after failure: %s", db_err)


# ── File readers ─────────────────────────────────────────────────────────────


def _read_file(file_path: str, file_type: str) -> Optional[gpd.GeoDataFrame]:
    """Dispatch to the correct reader based on *file_type*."""
    if file_type == "shapefile":
        return _read_shapefile(file_path)
    if file_type == "kml":
        return _read_kml(file_path)
    raise ValueError(f"Unsupported file type: {file_type}")


def _read_shapefile(file_path: str) -> Optional[gpd.GeoDataFrame]:
    """Extract a ``.zip`` archive and read the first ``.shp`` inside it."""
    extract_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            zf.extractall(extract_dir)

        # Walk extracted tree looking for .shp
        shp_files: list[str] = []
        for root, _dirs, files in os.walk(extract_dir):
            for fname in files:
                if fname.lower().endswith(".shp"):
                    shp_files.append(os.path.join(root, fname))

        if not shp_files:
            raise ValueError("No .shp file found inside the uploaded ZIP archive")

        logger.info("Reading shapefile: %s", shp_files[0])
        return gpd.read_file(shp_files[0])
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def _read_kml(file_path: str) -> Optional[gpd.GeoDataFrame]:
    """Read a KML file using Fiona's KML driver."""
    # Enable the KML driver (not enabled by default in all Fiona builds)
    fiona.drvsupport.supported_drivers["KML"] = "r"
    logger.info("Reading KML file: %s", file_path)
    return gpd.read_file(file_path, driver="KML")


# ── Helpers ──────────────────────────────────────────────────────────────────


def _extract_properties(row, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
    """Pull non-geometry columns from *row* into a JSON-safe dict."""
    props: Dict[str, Any] = {}
    geom_col = gdf.geometry.name

    for col in gdf.columns:
        if col == "geometry" or col == geom_col:
            continue
        val = row[col]
        # numpy scalar → Python native
        if hasattr(val, "item"):
            val = val.item()
        elif val is not None and not isinstance(val, (str, int, float, bool)):
            val = str(val)
        props[col] = val

    return props


def _mark_failed(db: Session, geo_file: GeoFile, message: str) -> None:
    """Set *geo_file* status to FAILED and commit."""
    geo_file.status = FileStatus.FAILED
    geo_file.error_message = message
    geo_file.processed_at = datetime.now(timezone.utc)
    db.commit()
    logger.warning("File %s marked FAILED: %s", geo_file.id, message)
