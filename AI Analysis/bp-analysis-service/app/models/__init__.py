# models/__init__.py
"""Data models for requests and responses."""

from .requests import (
    TimeRange,
    AnalysisRequest,
    ForecastRequest,
    BloodPressureReading,
    Medication,
    MedicationLog,
    LifestyleEntry,
    PatientProfile,
)

from .responses import (
    Insight,
    InsightsResponse,
    RiskFactor,
    RiskAssessment,
    TrendPrediction,
    TrendPredictionsResponse,
    HealthCategory,
    HealthScore,
    Pattern,
    PatternAnalysis,
    Correlation,
    CorrelationAnalysis,
    HistoricalDataPoint,
    ForecastDataPoint,
    TimeSeriesForecast,
    ErrorDetail,
    ErrorResponse,
)

__all__ = [
    # Requests
    "TimeRange",
    "AnalysisRequest",
    "ForecastRequest",
    "BloodPressureReading",
    "Medication",
    "MedicationLog",
    "LifestyleEntry",
    "PatientProfile",
    # Responses
    "Insight",
    "InsightsResponse",
    "RiskFactor",
    "RiskAssessment",
    "TrendPrediction",
    "TrendPredictionsResponse",
    "HealthCategory",
    "HealthScore",
    "Pattern",
    "PatternAnalysis",
    "Correlation",
    "CorrelationAnalysis",
    "HistoricalDataPoint",
    "ForecastDataPoint",
    "TimeSeriesForecast",
    "ErrorDetail",
    "ErrorResponse",
]
