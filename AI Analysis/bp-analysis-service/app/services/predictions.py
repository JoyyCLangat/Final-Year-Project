# predictions.py
"""Trend predictions service."""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import numpy as np

from app.models import TrendPrediction, TrendPredictionsResponse
from app.utils import Database
from app.errors import InsufficientDataError, PatientNotFoundError
from app.config import get_settings


async def calculate_predictions(patient_id: str, days: int = 30) -> List[TrendPrediction]:
    """
    Calculate trend predictions for blood pressure metrics.
    
    Returns list of TrendPrediction matching frontend interface:
    - metric: string (e.g., "Systolic BP")
    - currentValue: number
    - predictedValue: number
    - confidence: number (0-100)
    - timeframe: string (e.g., "30 days")
    - trend: 'improving' | 'stable' | 'worsening'
    """
    settings = get_settings()
    
    # Fetch patient data
    patient = Database.fetch_patient(patient_id)
    if not patient:
        raise PatientNotFoundError(patient_id)
    
    readings = Database.fetch_blood_pressure_readings(patient_id, days)
    
    if len(readings) < settings.min_readings_for_analysis:
        raise InsufficientDataError(
            message=f"Not enough readings for predictions (have {len(readings)}, need {settings.min_readings_for_analysis})",
            details={"readings_count": len(readings), "minimum_required": settings.min_readings_for_analysis}
        )
    
    predictions = []
    
    # Calculate Systolic BP prediction
    systolic_prediction = _calculate_metric_prediction(
        readings=readings,
        metric_key="systolic",
        metric_name="Systolic BP",
        timeframe_days=30
    )
    predictions.append(systolic_prediction)
    
    # Calculate Diastolic BP prediction
    diastolic_prediction = _calculate_metric_prediction(
        readings=readings,
        metric_key="diastolic",
        metric_name="Diastolic BP",
        timeframe_days=30
    )
    predictions.append(diastolic_prediction)
    
    # Calculate Pulse prediction if available
    readings_with_pulse = [r for r in readings if r.get("pulse")]
    if len(readings_with_pulse) >= 5:
        pulse_prediction = _calculate_metric_prediction(
            readings=readings_with_pulse,
            metric_key="pulse",
            metric_name="Heart Rate",
            timeframe_days=30
        )
        predictions.append(pulse_prediction)
    
    return predictions


def _calculate_metric_prediction(
    readings: List[Dict],
    metric_key: str,
    metric_name: str,
    timeframe_days: int = 30
) -> TrendPrediction:
    """Calculate prediction for a single metric."""
    
    # Sort readings by date (oldest first for regression)
    sorted_readings = sorted(readings, key=lambda x: x["measurement_date"])
    
    # Extract values
    values = [r[metric_key] for r in sorted_readings]
    n = len(values)
    
    # Calculate current value (average of last 7 readings)
    recent_values = values[-7:] if len(values) >= 7 else values
    current_value = sum(recent_values) / len(recent_values)
    
    # Simple linear regression
    x = np.array(range(n))
    y = np.array(values)
    
    # Calculate slope and intercept
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    
    if denominator == 0:
        slope = 0
    else:
        slope = numerator / denominator
    
    intercept = y_mean - slope * x_mean
    
    # Project forward
    # Estimate readings per day from the data
    if len(sorted_readings) >= 2:
        first_date = _parse_date(sorted_readings[0]["measurement_date"])
        last_date = _parse_date(sorted_readings[-1]["measurement_date"])
        days_span = (last_date - first_date).days or 1
        readings_per_day = n / days_span
    else:
        readings_per_day = 1
    
    # Predicted value at timeframe
    future_x = n + (timeframe_days * readings_per_day)
    predicted_value = intercept + slope * future_x
    
    # Determine trend direction
    # For BP, negative slope = improving (going down is good)
    daily_change = slope * readings_per_day
    
    if metric_key in ["systolic", "diastolic"]:
        # For BP, decreasing is improving
        if daily_change < -0.3:
            trend = "improving"
        elif daily_change > 0.3:
            trend = "worsening"
        else:
            trend = "stable"
    else:
        # For heart rate, stable is generally good
        if abs(daily_change) < 0.5:
            trend = "stable"
        elif daily_change < 0:
            trend = "improving"
        else:
            trend = "worsening"
    
    # Calculate confidence based on data consistency
    if n > 1:
        # R-squared as confidence measure
        y_pred = intercept + slope * x
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Adjust confidence based on data amount and consistency
        data_factor = min(1.0, n / 30)  # More data = more confidence
        confidence = int(max(30, min(95, r_squared * 100 * data_factor)))
    else:
        confidence = 30
    
    # Ensure predicted value is reasonable
    if metric_key == "systolic":
        predicted_value = max(80, min(200, predicted_value))
    elif metric_key == "diastolic":
        predicted_value = max(50, min(130, predicted_value))
    elif metric_key == "pulse":
        predicted_value = max(40, min(150, predicted_value))
    
    return TrendPrediction(
        metric=metric_name,
        currentValue=round(current_value, 1),
        predictedValue=round(predicted_value, 1),
        confidence=confidence,
        timeframe=f"{timeframe_days} days",
        trend=trend
    )


def _parse_date(date_value) -> datetime:
    """Parse date from various formats."""
    if isinstance(date_value, datetime):
        return date_value
    if isinstance(date_value, str):
        # Handle ISO format with or without timezone
        date_str = date_value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            # Try without timezone
            return datetime.fromisoformat(date_str.split("+")[0])
    return datetime.now()
