# responses.py
"""Response models matching frontend TypeScript interfaces exactly."""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ============================================
# SmartInsights Component Models
# ============================================

class Insight(BaseModel):
    """Matches frontend Insight interface."""
    id: str
    type: Literal["success", "warning", "info", "danger"]
    title: str
    message: str
    priority: int = Field(ge=1, le=5)
    timestamp: str  # ISO date format
    recommendations: Optional[List[str]] = None


class InsightsResponse(BaseModel):
    """Response for /api/v1/analysis/insights endpoint."""
    insights: List[Insight]


# ============================================
# PredictiveAnalyticsDashboard Models
# ============================================

class RiskFactor(BaseModel):
    """Individual risk factor."""
    name: str
    impact: Literal["low", "moderate", "high"]
    description: str


class RiskAssessment(BaseModel):
    """Matches frontend RiskAssessment interface."""
    overallRisk: Literal["low", "moderate", "high", "critical"]
    riskScore: int = Field(ge=0, le=100)
    factors: List[RiskFactor]
    recommendations: List[str]


class TrendPrediction(BaseModel):
    """Matches frontend TrendPrediction interface."""
    metric: str
    currentValue: float
    predictedValue: float
    confidence: int = Field(ge=0, le=100)
    timeframe: str
    trend: Literal["improving", "stable", "worsening"]


class TrendPredictionsResponse(BaseModel):
    """Response for /api/v1/analysis/predictions endpoint."""
    predictions: List[TrendPrediction]


class HealthCategory(BaseModel):
    """Individual health category score."""
    name: str
    score: int = Field(ge=0, le=100)
    status: Literal["excellent", "good", "fair", "poor"]


class HealthScore(BaseModel):
    """Matches frontend HealthScore interface."""
    overall: int = Field(ge=0, le=100)
    categories: List[HealthCategory]
    improvementAreas: List[str]


# ============================================
# AdvancedVisualizationHub Models
# ============================================

class Pattern(BaseModel):
    """Individual pattern detected."""
    type: str
    frequency: str
    severity: Literal["low", "moderate", "high"]
    description: str


class PatternAnalysis(BaseModel):
    """Matches frontend PatternAnalysis interface."""
    patterns: List[Pattern]


class Correlation(BaseModel):
    """Individual correlation between factors."""
    factor1: str
    factor2: str
    correlation: float = Field(ge=-1, le=1)
    strength: Literal["weak", "moderate", "strong"]
    direction: Literal["positive", "negative"]


class CorrelationAnalysis(BaseModel):
    """Matches frontend CorrelationAnalysis interface."""
    correlations: List[Correlation]


class HistoricalDataPoint(BaseModel):
    """Historical data point for time series."""
    date: str  # ISO format
    value: float


class ForecastDataPoint(BaseModel):
    """Forecast data point with confidence bounds."""
    date: str  # ISO format
    predicted: float
    upperBound: float
    lowerBound: float


class TimeSeriesForecast(BaseModel):
    """Matches frontend TimeSeriesForecast interface."""
    metric: str
    historical: List[HistoricalDataPoint]
    forecast: List[ForecastDataPoint]


# ============================================
# Error Response Model
# ============================================

class ErrorDetail(BaseModel):
    """Error detail structure."""
    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: ErrorDetail
