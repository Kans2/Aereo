"""Miscellaneous file-system helpers."""

import os
import logging

logger = logging.getLogger(__name__)


def ensure_directory(path: str) -> None:
    """Create *path* (and parents) if it does not exist."""
    os.makedirs(path, exist_ok=True)


def cleanup_file(path: str) -> None:
    """Delete a file, logging but swallowing errors."""
    try:
        if os.path.isfile(path):
            os.remove(path)
            logger.debug("Removed file: %s", path)
    except OSError as exc:
        logger.warning("Could not remove file %s: %s", path, exc)
