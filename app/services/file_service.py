"""File service — upload validation, storage, and file-type detection."""

import logging
import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings

logger = logging.getLogger(__name__)


def validate_file(file: UploadFile) -> tuple:
    """Validate the uploaded file and return ``(extension, file_type)``.

    Raises
    ------
    ValueError
        If the filename is missing or the extension is not supported.
    """
    if not file.filename:
        raise ValueError("Filename is required")

    filename_lower = file.filename.lower()

    if filename_lower.endswith(".zip"):
        return ".zip", "shapefile"
    if filename_lower.endswith(".kml"):
        return ".kml", "kml"

    ext = Path(filename_lower).suffix or "(none)"
    raise ValueError(
        f"Unsupported file format: {ext}. "
        "Accepted formats: .zip (Shapefile), .kml"
    )


async def save_upload(file: UploadFile) -> tuple:
    """Save *file* to the upload directory.

    Returns
    -------
    tuple
        ``(saved_file_path, file_type)``

    Raises
    ------
    ValueError
        If validation fails or the file exceeds the size limit.
    """
    ext, file_type = validate_file(file)

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Generate a unique on-disk name to avoid collisions
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    # Read file content
    content = await file.read()

    # Enforce size limit
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise ValueError(
            f"File size ({len(content) / 1024 / 1024:.1f} MB) exceeds "
            f"the maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB"
        )

    # Persist to disk
    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(
        "Saved upload: %s → %s (%d bytes)", file.filename, file_path, len(content)
    )
    return file_path, file_type
