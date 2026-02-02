# handlers.py
"""Error handling utilities."""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional


class AnalysisError(Exception):
    """Base exception for analysis errors."""
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[dict] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class InsufficientDataError(AnalysisError):
    """Raised when there's not enough data for analysis."""
    
    def __init__(self, message: str = "Not enough data for analysis", details: Optional[dict] = None):
        super().__init__(
            code="INSUFFICIENT_DATA",
            message=message,
            status_code=400,
            details=details
        )


class PatientNotFoundError(AnalysisError):
    """Raised when patient is not found."""
    
    def __init__(self, patient_id: str):
        super().__init__(
            code="PATIENT_NOT_FOUND",
            message=f"Patient with ID {patient_id} not found",
            status_code=404,
            details={"patient_id": patient_id}
        )


class AnalysisFailedError(AnalysisError):
    """Raised when analysis fails."""
    
    def __init__(self, message: str = "Analysis failed", details: Optional[dict] = None):
        super().__init__(
            code="ANALYSIS_FAILED",
            message=message,
            status_code=500,
            details=details
        )


class DatabaseError(AnalysisError):
    """Raised when database operation fails."""
    
    def __init__(self, message: str = "Database operation failed", details: Optional[dict] = None):
        super().__init__(
            code="DATABASE_ERROR",
            message=message,
            status_code=500,
            details=details
        )


async def analysis_error_handler(request: Request, exc: AnalysisError) -> JSONResponse:
    """Handle AnalysisError exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error": str(exc)}
            }
        }
    )
