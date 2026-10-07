"""Custom exception classes for the Geospatial File Measurement API."""

from fastapi import HTTPException, status


class FileNotFoundError(HTTPException):
    """Raised when a requested file ID does not exist."""

    def __init__(self, file_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id '{file_id}' not found",
        )


class FileProcessingError(HTTPException):
    """Raised when file processing has failed."""

    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File processing failed: {message}",
        )


class FileStillProcessingError(HTTPException):
    """Raised when data is requested for a file that is still being processed."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="File is still being processed. Please try again later.",
        )


class UnsupportedFileFormatError(HTTPException):
    """Raised when an uploaded file has an unsupported format."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )
