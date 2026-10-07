"""GeoFile model — represents an uploaded geospatial file."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum as SQLEnum, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class FileStatus(str, enum.Enum):
    """Processing status of an uploaded file."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class GeoFile(Base):
    """Stores metadata for each uploaded geospatial file."""

    __tablename__ = "geo_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False, index=True)
    original_crs = Column(String(100), nullable=True)
    file_type = Column(String(20), nullable=False)  # "shapefile" | "kml"
    feature_count = Column(Integer, default=0)
    status = Column(
        SQLEnum(FileStatus),
        default=FileStatus.PENDING,
        nullable=False,
        index=True,
    )
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    features = relationship(
        "Feature",
        back_populates="geo_file",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<GeoFile {self.filename} ({self.status.value})>"
