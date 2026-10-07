"""Pydantic schemas for file-related API responses."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response returned immediately after a file is uploaded."""

    id: UUID = Field(..., description="Unique identifier for the uploaded file")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Current processing status")
    uploaded_at: datetime = Field(..., description="Upload timestamp (UTC)")

    model_config = {"from_attributes": True}


class FileInfoResponse(BaseModel):
    """Detailed information about an uploaded geospatial file."""

    id: UUID = Field(..., description="Unique identifier")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="Detected file type (shapefile or kml)")
    feature_count: int = Field(..., description="Number of features extracted")
    crs: Optional[str] = Field(None, description="Original coordinate reference system")
    status: str = Field(..., description="Processing status")
    uploaded_at: datetime = Field(..., description="Upload timestamp (UTC)")
    processed_at: Optional[datetime] = Field(
        None, description="Processing completion timestamp (UTC)"
    )
    error_message: Optional[str] = Field(
        None, description="Error details if processing failed"
    )

    model_config = {"from_attributes": True}
