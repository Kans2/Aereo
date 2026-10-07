"""Feature model — represents a single geospatial feature extracted from a file."""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Feature(Base):
    """Stores individual features with their geometries and measurements."""

    __tablename__ = "features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("geo_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_index = Column(Integer, nullable=False)
    geometry_type = Column(String(50), nullable=False)
    geometry_wkt = Column(Text, nullable=True)
    original_crs = Column(String(100), nullable=True)
    projected_crs = Column(String(100), nullable=True)
    properties = Column(JSON, nullable=True, default=dict)
    area_sq_meters = Column(Float, nullable=True)
    length_meters = Column(Float, nullable=True)
    measurement_supported = Column(Boolean, default=False, nullable=False)
    measurement_note = Column(String(500), nullable=True)

    # Relationships
    geo_file = relationship("GeoFile", back_populates="features")

    def __repr__(self) -> str:
        return (
            f"<Feature idx={self.feature_index} "
            f"type={self.geometry_type} "
            f"supported={self.measurement_supported}>"
        )
