"""Pydantic schemas for feature measurement API responses."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FeatureMeasurement(BaseModel):
    """Measurement data for a single geospatial feature."""

    feature_index: int = Field(..., description="Zero-based index of the feature")
    geometry_type: str = Field(..., description="OGC geometry type name")
    properties: Optional[Dict[str, Any]] = Field(
        None, description="Feature attributes/properties from the source file"
    )
    area_sq_meters: Optional[float] = Field(
        None, description="Area in square meters (Polygon/MultiPolygon only)"
    )
    length_meters: Optional[float] = Field(
        None, description="Length in meters (LineString/MultiLineString only)"
    )
    measurement_supported: bool = Field(
        ..., description="Whether measurement was calculated for this geometry type"
    )
    measurement_note: Optional[str] = Field(
        None, description="Additional notes about the measurement"
    )

    model_config = {"from_attributes": True}


class MeasurementsResponse(BaseModel):
    """Aggregated measurement response for all features in a file."""

    file_id: UUID = Field(..., description="ID of the source file")
    filename: str = Field(..., description="Original filename")
    total_features: int = Field(..., description="Total number of features processed")
    measurements: List[FeatureMeasurement] = Field(
        ..., description="Per-feature measurement results"
    )
