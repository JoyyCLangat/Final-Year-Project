# services/__init__.py
"""Analysis services module."""

from .insights import generate_insights
from .risk_assessment import calculate_risk_assessment
from .predictions import calculate_predictions
from .health_score import calculate_health_score
from .patterns import analyze_patterns
from .correlations import analyze_correlations
from .forecast import generate_forecast

__all__ = [
    "generate_insights",
    "calculate_risk_assessment",
    "calculate_predictions",
    "calculate_health_score",
    "analyze_patterns",
    "analyze_correlations",
    "generate_forecast",
]
