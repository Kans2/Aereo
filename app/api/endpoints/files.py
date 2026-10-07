"""
/api/files/ endpoints
─────────────────────
POST   /api/files/                  Upload a geospatial file
GET    /api/files/                  List all uploaded files
GET    /api/files/{file_id}/        File metadata
GET    /api/files/{file_id}/measurements/   Feature measurements
"""

import logging
from typing import List
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.feature import Feature
from app.models.file import FileStatus, GeoFile
from app.schemas.feature import FeatureMeasurement, MeasurementsResponse
from app.schemas.file import FileInfoResponse, FileUploadResponse
from app.services.file_service import save_upload, validate_file
from app.services.geo_processor import process_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["Files"])


# ── helpers ──────────────────────────────────────────────────────────────────


def _run_processing(file_id: str, file_path: str, file_type: str) -> None:
    """Wrapper executed inside BackgroundTasks with its own DB session."""
    db = SessionLocal()
    try:
        process_file(db, file_id, file_path, file_type)
    finally:
        db.close()


def _get_file_or_404(db: Session, file_id: UUID) -> GeoFile:
    """Fetch a GeoFile or raise 404."""
    geo_file = db.query(GeoFile).filter(GeoFile.id == file_id).first()
    if geo_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id '{file_id}' not found",
        )
    return geo_file


# ── endpoints ────────────────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a geospatial file",
    description=(
        "Accepts a `.zip` (Shapefile) or `.kml` file. The file is persisted "
        "and a background task is spawned to parse features and compute "
        "measurements. Returns immediately with a file ID and a `PENDING` status."
    ),
)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(
        ..., description="Geospatial file — .zip (Shapefile) or .kml"
    ),
    db: Session = Depends(get_db),
):
    # Validate extension before reading the body
    try:
        validate_file(file)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )

    # Save file to disk
    try:
        file_path, file_type = await save_upload(file)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )

    # Create DB record
    geo_file = GeoFile(
        filename=file.filename,
        file_type=file_type,
        status=FileStatus.PENDING,
    )
    db.add(geo_file)
    db.commit()
    db.refresh(geo_file)

    # Kick off async processing
    background_tasks.add_task(
        _run_processing, str(geo_file.id), file_path, file_type
    )

    logger.info("File %s queued for processing (id=%s)", file.filename, geo_file.id)
    return FileUploadResponse(
        id=geo_file.id,
        filename=geo_file.filename,
        status=geo_file.status.value,
        uploaded_at=geo_file.uploaded_at,
    )


@router.get(
    "/",
    response_model=List[FileInfoResponse],
    summary="List all uploaded files",
    description="Returns metadata for every uploaded file, newest first.",
)
def list_files(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    db: Session = Depends(get_db),
):
    files = (
        db.query(GeoFile)
        .order_by(GeoFile.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        FileInfoResponse(
            id=f.id,
            filename=f.filename,
            file_type=f.file_type,
            feature_count=f.feature_count,
            crs=f.original_crs,
            status=f.status.value,
            uploaded_at=f.uploaded_at,
            processed_at=f.processed_at,
            error_message=f.error_message,
        )
        for f in files
    ]


@router.get(
    "/{file_id}/",
    response_model=FileInfoResponse,
    summary="Get file information",
    description="Returns detailed metadata about a single uploaded file.",
)
def get_file_info(
    file_id: UUID,
    db: Session = Depends(get_db),
):
    geo_file = _get_file_or_404(db, file_id)
    return FileInfoResponse(
        id=geo_file.id,
        filename=geo_file.filename,
        file_type=geo_file.file_type,
        feature_count=geo_file.feature_count,
        crs=geo_file.original_crs,
        status=geo_file.status.value,
        uploaded_at=geo_file.uploaded_at,
        processed_at=geo_file.processed_at,
        error_message=geo_file.error_message,
    )


@router.get(
    "/{file_id}/measurements/",
    response_model=MeasurementsResponse,
    summary="Get feature measurements",
    description=(
        "Returns per-feature measurements (area for polygons, length for "
        "line strings) for a successfully processed file."
    ),
)
def get_measurements(
    file_id: UUID,
    db: Session = Depends(get_db),
):
    geo_file = _get_file_or_404(db, file_id)

    # Guard: still processing
    if geo_file.status in (FileStatus.PENDING, FileStatus.PROCESSING):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File is still being processed. Please try again later.",
        )

    # Guard: processing failed
    if geo_file.status == FileStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File processing failed: {geo_file.error_message}",
        )

    features = (
        db.query(Feature)
        .filter(Feature.file_id == file_id)
        .order_by(Feature.feature_index)
        .all()
    )

    return MeasurementsResponse(
        file_id=geo_file.id,
        filename=geo_file.filename,
        total_features=geo_file.feature_count,
        measurements=[
            FeatureMeasurement(
                feature_index=f.feature_index,
                geometry_type=f.geometry_type,
                properties=f.properties,
                area_sq_meters=f.area_sq_meters,
                length_meters=f.length_meters,
                measurement_supported=f.measurement_supported,
                measurement_note=f.measurement_note,
            )
            for f in features
        ],
    )
