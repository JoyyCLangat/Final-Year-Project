# errors/__init__.py
"""Error handling module."""

from .handlers import (
    AnalysisError,
    InsufficientDataError,
    PatientNotFoundError,
    AnalysisFailedError,
    DatabaseError,
    analysis_error_handler,
    generic_error_handler,
)

__all__ = [
    "AnalysisError",
    "InsufficientDataError",
    "PatientNotFoundError",
    "AnalysisFailedError",
    "DatabaseError",
    "analysis_error_handler",
    "generic_error_handler",
]
