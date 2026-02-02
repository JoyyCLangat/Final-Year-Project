# forecast.py
"""Time series forecast service."""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import numpy as np

from app.models import TimeSeriesForecast, HistoricalDataPoint, ForecastDataPoint
from app.utils import Database
from app.errors import InsufficientDataError, PatientNotFoundError
from app.config import get_settings


async def generate_forecast(
    patient_id: str,
    metric: str = "systolic",
    forecast_days: int = 30,
    history_days: int = 60
) -> TimeSeriesForecast:
    """
    Generate time series forecast for blood pressure.
    
    Returns TimeSeriesForecast matching frontend interface:
    - metric: string
    - historical: Array of {date, value}
    - forecast: Array of {date, predicted, upperBound, lowerBound}
    """
    settings = get_settings()
    
    # Validate metric
    if metric not in ["systolic", "diastolic", "pulse"]:
        metric = "systolic"
    
    metric_name = {
        "systolic": "Systolic BP",
        "diastolic": "Diastolic BP",
        "pulse": "Heart Rate"
    }.get(metric, "Systolic BP")
    
    # Fetch patient data
    patient = Database.fetch_patient(patient_id)
    if not patient:
        raise PatientNotFoundError(patient_id)
    
    readings = Database.fetch_blood_pressure_readings(patient_id, history_days)
    
    if len(readings) < settings.min_readings_for_analysis:
        raise InsufficientDataError(
            message=f"Not enough readings for forecast (have {len(readings)}, need {settings.min_readings_for_analysis})",
            details={"readings_count": len(readings), "minimum_required": settings.min_readings_for_analysis}
        )
    
    # Build historical data (daily averages)
    historical = _build_historical_data(readings, metric)
    
    if len(historical) < 7:
        raise InsufficientDataError(
            message="Not enough daily data points for forecast",
            details={"days_with_data": len(historical), "minimum_required": 7}
        )
    
    # Generate forecast
    forecast = _generate_forecast_points(historical, forecast_days, metric)
    
    return TimeSeriesForecast(
        metric=metric_name,
        historical=historical,
        forecast=forecast
    )


def _build_historical_data(readings: List[Dict], metric: str) -> List[HistoricalDataPoint]:
    """Build daily historical data points."""
    from collections import defaultdict
    
    # Group readings by date
    daily_values = defaultdict(list)
    
    for r in readings:
        date = _parse_date(r["measurement_date"]).date()
        value = r.get(metric)
        if value is not None:
            daily_values[date].append(value)
    
    # Calculate daily averages
    historical = []
    for date in sorted(daily_values.keys()):
        values = daily_values[date]
        avg_value = sum(values) / len(values)
        historical.append(HistoricalDataPoint(
            date=date.isoformat(),
            value=round(avg_value, 1)
        ))
    
    return historical


def _generate_forecast_points(
    historical: List[HistoricalDataPoint],
    forecast_days: int,
    metric: str
) -> List[ForecastDataPoint]:
    """Generate forecast points using linear regression with confidence bounds."""
    
    # Extract values
    values = [h.value for h in historical]
    n = len(values)
    
    # Simple linear regression
    x = np.array(range(n))
    y = np.array(values)
    
    # Calculate regression parameters
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    
    if denominator == 0:
        slope = 0
        intercept = y_mean
    else:
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
    
    # Calculate standard error for prediction intervals
    y_pred_historical = intercept + slope * x
    residuals = y - y_pred_historical
    std_error = np.std(residuals) if len(residuals) > 2 else 10
    
    # Get the last date from historical data
    last_date = datetime.fromisoformat(historical[-1].date)
    
    # Generate forecast points
    forecast = []
    
    # Confidence interval expands over time
    for i in range(1, forecast_days + 1):
        forecast_date = last_date + timedelta(days=i)
        x_future = n + i - 1
        
        # Predicted value
        predicted = intercept + slope * x_future
        
        # Confidence bounds (expand with time)
        # Use 95% confidence interval approximation
        margin = 1.96 * std_error * (1 + (i / forecast_days) * 0.5)
        
        # Apply bounds based on metric
        if metric == "systolic":
            predicted = max(80, min(200, predicted))
            upper = min(220, predicted + margin)
            lower = max(70, predicted - margin)
        elif metric == "diastolic":
            predicted = max(50, min(130, predicted))
            upper = min(150, predicted + margin)
            lower = max(40, predicted - margin)
        else:  # pulse
            predicted = max(40, min(150, predicted))
            upper = min(180, predicted + margin)
            lower = max(30, predicted - margin)
        
        forecast.append(ForecastDataPoint(
            date=forecast_date.date().isoformat(),
            predicted=round(predicted, 1),
            upperBound=round(upper, 1),
            lowerBound=round(lower, 1)
        ))
    
    return forecast


def _parse_date(date_value) -> datetime:
    """Parse date from various formats."""
    if isinstance(date_value, datetime):
        return date_value
    if isinstance(date_value, str):
        date_str = date_value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            return datetime.fromisoformat(date_str.split("+")[0])
    return datetime.now()
