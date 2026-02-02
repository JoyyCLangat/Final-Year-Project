# correlations.py
"""Correlation analysis service."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import math

from app.models import CorrelationAnalysis, Correlation
from app.utils import Database
from app.errors import InsufficientDataError, PatientNotFoundError
from app.config import get_settings


async def analyze_correlations(patient_id: str, days: int = 30) -> CorrelationAnalysis:
    """
    Analyze correlations between lifestyle factors and blood pressure.
    
    Returns CorrelationAnalysis matching frontend interface:
    - correlations: Array of {factor1, factor2, correlation, strength, direction}
    """
    settings = get_settings()
    
    # Fetch patient data
    patient = Database.fetch_patient(patient_id)
    if not patient:
        raise PatientNotFoundError(patient_id)
    
    readings = Database.fetch_blood_pressure_readings(patient_id, days)
    lifestyle = Database.fetch_lifestyle_entries(patient_id, days)
    
    if len(readings) < settings.min_readings_for_analysis:
        raise InsufficientDataError(
            message=f"Not enough data for correlation analysis",
            details={"readings_count": len(readings), "minimum_required": settings.min_readings_for_analysis}
        )
    
    correlations: List[Correlation] = []
    
    # Build daily data map
    daily_data = _build_daily_data(readings, lifestyle)
    
    if len(daily_data) < 5:
        raise InsufficientDataError(
            message="Not enough daily data points for correlation analysis",
            details={"days_with_data": len(daily_data), "minimum_required": 5}
        )
    
    # Extract data series
    dates = sorted(daily_data.keys())
    
    # Analyze correlations with various factors
    factor_correlations = []
    
    # 1. Sodium intake correlation
    sodium_corr = _calculate_factor_correlation(daily_data, dates, "systolic", "sodium_mg")
    if sodium_corr:
        factor_correlations.append(("Sodium Intake", "Systolic BP", sodium_corr))
    
    # 2. Physical activity correlation
    activity_corr = _calculate_factor_correlation(daily_data, dates, "systolic", "physical_activity")
    if activity_corr:
        factor_correlations.append(("Physical Activity", "Systolic BP", activity_corr))
    
    # 3. Sleep duration correlation
    sleep_corr = _calculate_factor_correlation(daily_data, dates, "systolic", "sleep_duration")
    if sleep_corr:
        factor_correlations.append(("Sleep Duration", "Systolic BP", sleep_corr))
    
    # 4. Stress level correlation (convert to numeric)
    stress_corr = _calculate_stress_correlation(daily_data, dates)
    if stress_corr:
        factor_correlations.append(("Stress Level", "Systolic BP", stress_corr))
    
    # 5. Weight correlation
    weight_corr = _calculate_factor_correlation(daily_data, dates, "systolic", "weight")
    if weight_corr:
        factor_correlations.append(("Body Weight", "Systolic BP", weight_corr))
    
    # 6. Water intake correlation
    water_corr = _calculate_factor_correlation(daily_data, dates, "systolic", "water_intake")
    if water_corr:
        factor_correlations.append(("Water Intake", "Systolic BP", water_corr))
    
    # 7. Caffeine correlation
    caffeine_corr = _calculate_factor_correlation(daily_data, dates, "systolic", "caffeine_intake")
    if caffeine_corr:
        factor_correlations.append(("Caffeine Intake", "Systolic BP", caffeine_corr))
    
    # 8. Alcohol correlation
    alcohol_corr = _calculate_factor_correlation(daily_data, dates, "systolic", "alcohol_consumption")
    if alcohol_corr:
        factor_correlations.append(("Alcohol Consumption", "Systolic BP", alcohol_corr))
    
    # 9. Diastolic vs Systolic correlation
    dias_sys_corr = _calculate_factor_correlation(daily_data, dates, "systolic", "diastolic")
    if dias_sys_corr:
        factor_correlations.append(("Diastolic BP", "Systolic BP", dias_sys_corr))
    
    # 10. Pulse vs Systolic correlation
    pulse_corr = _calculate_factor_correlation(daily_data, dates, "systolic", "pulse")
    if pulse_corr:
        factor_correlations.append(("Heart Rate", "Systolic BP", pulse_corr))
    
    # Convert to Correlation objects
    for factor1, factor2, corr_value in factor_correlations:
        strength = _correlation_strength(corr_value)
        direction = "positive" if corr_value > 0 else "negative"
        
        correlations.append(Correlation(
            factor1=factor1,
            factor2=factor2,
            correlation=round(corr_value, 3),
            strength=strength,
            direction=direction
        ))
    
    # Sort by absolute correlation value (strongest first)
    correlations.sort(key=lambda x: abs(x.correlation), reverse=True)
    
    return CorrelationAnalysis(correlations=correlations)


def _build_daily_data(readings: List[Dict], lifestyle: List[Dict]) -> Dict[str, Dict]:
    """Build a daily data map combining readings and lifestyle."""
    daily_data = defaultdict(dict)
    
    # Add readings data (average per day)
    readings_by_date = defaultdict(list)
    for r in readings:
        date = _parse_date(r["measurement_date"]).date().isoformat()
        readings_by_date[date].append(r)
    
    for date, day_readings in readings_by_date.items():
        daily_data[date]["systolic"] = sum(r["systolic"] for r in day_readings) / len(day_readings)
        daily_data[date]["diastolic"] = sum(r["diastolic"] for r in day_readings) / len(day_readings)
        
        pulse_readings = [r["pulse"] for r in day_readings if r.get("pulse")]
        if pulse_readings:
            daily_data[date]["pulse"] = sum(pulse_readings) / len(pulse_readings)
    
    # Add lifestyle data
    for entry in lifestyle:
        date = entry.get("entry_date")
        if date:
            for key in ["physical_activity", "sleep_duration", "stress_level", 
                       "water_intake", "weight", "sodium_mg", "caffeine_intake",
                       "alcohol_consumption", "salt_intake"]:
                if entry.get(key) is not None:
                    daily_data[date][key] = entry[key]
    
    return dict(daily_data)


def _calculate_factor_correlation(
    daily_data: Dict[str, Dict],
    dates: List[str],
    outcome_key: str,
    factor_key: str
) -> Optional[float]:
    """Calculate Pearson correlation between two factors."""
    # Get paired data points
    pairs = []
    for date in dates:
        outcome = daily_data[date].get(outcome_key)
        factor = daily_data[date].get(factor_key)
        if outcome is not None and factor is not None:
            pairs.append((outcome, factor))
    
    if len(pairs) < 5:
        return None
    
    # Calculate Pearson correlation
    n = len(pairs)
    sum_x = sum(p[0] for p in pairs)
    sum_y = sum(p[1] for p in pairs)
    sum_xy = sum(p[0] * p[1] for p in pairs)
    sum_x2 = sum(p[0] ** 2 for p in pairs)
    sum_y2 = sum(p[1] ** 2 for p in pairs)
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator_sq = (n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)
    
    if denominator_sq <= 0:
        return None
    
    denominator = math.sqrt(denominator_sq)
    
    if denominator == 0:
        return None
    
    correlation = numerator / denominator
    
    # Return None for very weak correlations
    if abs(correlation) < 0.1:
        return None
    
    return correlation


def _calculate_stress_correlation(daily_data: Dict[str, Dict], dates: List[str]) -> Optional[float]:
    """Calculate correlation between stress level and systolic BP."""
    # Convert stress to numeric
    stress_map = {"low": 1, "moderate": 2, "high": 3, "severe": 4}
    
    pairs = []
    for date in dates:
        systolic = daily_data[date].get("systolic")
        stress = daily_data[date].get("stress_level")
        if systolic is not None and stress in stress_map:
            pairs.append((systolic, stress_map[stress]))
    
    if len(pairs) < 5:
        return None
    
    # Calculate correlation
    n = len(pairs)
    sum_x = sum(p[0] for p in pairs)
    sum_y = sum(p[1] for p in pairs)
    sum_xy = sum(p[0] * p[1] for p in pairs)
    sum_x2 = sum(p[0] ** 2 for p in pairs)
    sum_y2 = sum(p[1] ** 2 for p in pairs)
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator_sq = (n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)
    
    if denominator_sq <= 0:
        return None
    
    denominator = math.sqrt(denominator_sq)
    
    if denominator == 0:
        return None
    
    correlation = numerator / denominator
    
    if abs(correlation) < 0.1:
        return None
    
    return correlation


def _correlation_strength(correlation: float) -> str:
    """Determine correlation strength category."""
    abs_corr = abs(correlation)
    if abs_corr >= 0.7:
        return "strong"
    elif abs_corr >= 0.4:
        return "moderate"
    else:
        return "weak"


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
