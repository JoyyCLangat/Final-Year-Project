# patterns.py
"""Pattern analysis service."""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from app.models import PatternAnalysis, Pattern
from app.utils import Database
from app.errors import InsufficientDataError, PatientNotFoundError
from app.config import get_settings


async def analyze_patterns(patient_id: str, days: int = 30) -> PatternAnalysis:
    """
    Analyze blood pressure patterns for a patient.
    
    Returns PatternAnalysis matching frontend interface:
    - patterns: Array of {type, frequency, severity, description}
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
            message=f"Not enough readings for pattern analysis (have {len(readings)}, need {settings.min_readings_for_analysis})",
            details={"readings_count": len(readings), "minimum_required": settings.min_readings_for_analysis}
        )
    
    patterns: List[Pattern] = []
    
    # Analyze time-of-day patterns
    patterns.extend(_analyze_time_patterns(readings))
    
    # Analyze day-of-week patterns
    patterns.extend(_analyze_weekly_patterns(readings))
    
    # Analyze position patterns
    patterns.extend(_analyze_position_patterns(readings))
    
    # Analyze lifestyle correlations
    if lifestyle:
        patterns.extend(_analyze_lifestyle_patterns(readings, lifestyle))
    
    # Analyze variability patterns
    patterns.extend(_analyze_variability_patterns(readings))
    
    # Sort by severity (high first)
    severity_order = {"high": 0, "moderate": 1, "low": 2}
    patterns.sort(key=lambda x: severity_order.get(x.severity, 3))
    
    return PatternAnalysis(patterns=patterns[:10])  # Return top 10 patterns


def _analyze_time_patterns(readings: List[Dict]) -> List[Pattern]:
    """Analyze time-of-day patterns."""
    patterns = []
    
    # Group by time of day
    time_groups = defaultdict(list)
    for r in readings:
        time_of_day = r.get("time_of_day", "unknown")
        time_groups[time_of_day].append(r)
    
    # Calculate averages for each time period
    time_averages = {}
    for time, group in time_groups.items():
        if len(group) >= 3:
            avg_sys = sum(r["systolic"] for r in group) / len(group)
            time_averages[time] = avg_sys
    
    if len(time_averages) >= 2:
        # Check for morning spike
        morning_avg = time_averages.get("morning", 0)
        evening_avg = time_averages.get("evening", time_averages.get("night", 0))
        
        if morning_avg and evening_avg:
            if morning_avg - evening_avg > 15:
                morning_count = len(time_groups.get("morning", []))
                total_mornings = morning_count
                high_mornings = sum(1 for r in time_groups.get("morning", []) if r["systolic"] >= 140)
                frequency = f"{(high_mornings / total_mornings * 100):.0f}% of mornings" if total_mornings > 0 else "frequently"
                
                patterns.append(Pattern(
                    type="Morning Spike",
                    frequency=frequency,
                    severity="moderate" if morning_avg - evening_avg < 25 else "high",
                    description=f"Blood pressure averages {morning_avg:.0f}/{time_averages.get('morning', 0):.0f} mmHg in the morning, {morning_avg - evening_avg:.0f} points higher than evening"
                ))
            
            elif evening_avg - morning_avg > 15:
                patterns.append(Pattern(
                    type="Evening Elevation",
                    frequency="Most evenings",
                    severity="moderate",
                    description=f"Blood pressure tends to rise in the evening by {evening_avg - morning_avg:.0f} mmHg compared to morning"
                ))
    
    return patterns


def _analyze_weekly_patterns(readings: List[Dict]) -> List[Pattern]:
    """Analyze day-of-week patterns."""
    patterns = []
    
    # Group by day of week
    day_groups = defaultdict(list)
    for r in readings:
        date = _parse_date(r["measurement_date"])
        day_name = date.strftime("%A")
        day_groups[day_name].append(r)
    
    # Calculate averages
    day_averages = {}
    for day, group in day_groups.items():
        if len(group) >= 2:
            avg_sys = sum(r["systolic"] for r in group) / len(group)
            day_averages[day] = avg_sys
    
    if len(day_averages) >= 3:
        overall_avg = sum(day_averages.values()) / len(day_averages)
        
        # Weekend vs weekday comparison
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        weekend = ["Saturday", "Sunday"]
        
        weekday_avgs = [day_averages[d] for d in weekdays if d in day_averages]
        weekend_avgs = [day_averages[d] for d in weekend if d in day_averages]
        
        if weekday_avgs and weekend_avgs:
            weekday_avg = sum(weekday_avgs) / len(weekday_avgs)
            weekend_avg = sum(weekend_avgs) / len(weekend_avgs)
            
            if weekend_avg - weekday_avg > 8:
                patterns.append(Pattern(
                    type="Weekend Effect",
                    frequency="Most weekends",
                    severity="low",
                    description=f"Blood pressure tends to be {weekend_avg - weekday_avg:.0f} mmHg higher on weekends, possibly due to diet or activity changes"
                ))
            elif weekday_avg - weekend_avg > 8:
                patterns.append(Pattern(
                    type="Workweek Stress",
                    frequency="During work days",
                    severity="moderate",
                    description=f"Blood pressure averages {weekday_avg - weekend_avg:.0f} mmHg higher during weekdays, suggesting work-related stress"
                ))
        
        # Find highest day
        if day_averages:
            highest_day = max(day_averages, key=day_averages.get)
            lowest_day = min(day_averages, key=day_averages.get)
            diff = day_averages[highest_day] - day_averages[lowest_day]
            
            if diff > 12:
                patterns.append(Pattern(
                    type="Weekly Variation",
                    frequency=f"Every {highest_day}",
                    severity="low",
                    description=f"{highest_day}s tend to have higher readings ({day_averages[highest_day]:.0f} mmHg) compared to {lowest_day}s ({day_averages[lowest_day]:.0f} mmHg)"
                ))
    
    return patterns


def _analyze_position_patterns(readings: List[Dict]) -> List[Pattern]:
    """Analyze position-related patterns."""
    patterns = []
    
    # Group by position
    position_groups = defaultdict(list)
    for r in readings:
        position = r.get("position", "unknown")
        if position != "unknown":
            position_groups[position].append(r)
    
    # Calculate averages
    position_averages = {}
    for position, group in position_groups.items():
        if len(group) >= 3:
            avg_sys = sum(r["systolic"] for r in group) / len(group)
            position_averages[position] = avg_sys
    
    if "sitting" in position_averages and "standing" in position_averages:
        diff = position_averages["standing"] - position_averages["sitting"]
        
        if diff > 10:
            patterns.append(Pattern(
                type="Orthostatic Variation",
                frequency="When standing",
                severity="moderate",
                description=f"Blood pressure increases by {diff:.0f} mmHg when standing compared to sitting - discuss with your doctor"
            ))
        elif diff < -15:
            patterns.append(Pattern(
                type="Orthostatic Hypotension Risk",
                frequency="When standing",
                severity="high",
                description=f"Blood pressure drops by {abs(diff):.0f} mmHg when standing - this may cause dizziness"
            ))
    
    return patterns


def _analyze_lifestyle_patterns(readings: List[Dict], lifestyle: List[Dict]) -> List[Pattern]:
    """Analyze correlations with lifestyle factors."""
    patterns = []
    
    if not lifestyle:
        return patterns
    
    # Create date-indexed maps
    lifestyle_by_date = {entry.get("entry_date"): entry for entry in lifestyle}
    readings_by_date = defaultdict(list)
    
    for r in readings:
        date = _parse_date(r["measurement_date"]).date().isoformat()
        readings_by_date[date].append(r)
    
    # Analyze stress correlation
    high_stress_readings = []
    low_stress_readings = []
    
    for date, entry in lifestyle_by_date.items():
        if date in readings_by_date:
            stress = entry.get("stress_level")
            day_readings = readings_by_date[date]
            
            if stress in ["high", "severe"]:
                high_stress_readings.extend(day_readings)
            elif stress in ["low"]:
                low_stress_readings.extend(day_readings)
    
    if len(high_stress_readings) >= 3 and len(low_stress_readings) >= 3:
        high_stress_avg = sum(r["systolic"] for r in high_stress_readings) / len(high_stress_readings)
        low_stress_avg = sum(r["systolic"] for r in low_stress_readings) / len(low_stress_readings)
        
        if high_stress_avg - low_stress_avg > 10:
            patterns.append(Pattern(
                type="Stress Response",
                frequency="On high-stress days",
                severity="moderate",
                description=f"Blood pressure averages {high_stress_avg - low_stress_avg:.0f} mmHg higher on days with high stress"
            ))
    
    # Analyze exercise correlation
    exercise_days = []
    no_exercise_days = []
    
    for date, entry in lifestyle_by_date.items():
        if date in readings_by_date:
            activity = entry.get("physical_activity") or 0
            day_readings = readings_by_date[date]
            
            if activity >= 30:
                exercise_days.extend(day_readings)
            elif activity < 10:
                no_exercise_days.extend(day_readings)
    
    if len(exercise_days) >= 3 and len(no_exercise_days) >= 3:
        exercise_avg = sum(r["systolic"] for r in exercise_days) / len(exercise_days)
        no_exercise_avg = sum(r["systolic"] for r in no_exercise_days) / len(no_exercise_days)
        
        if no_exercise_avg - exercise_avg > 5:
            patterns.append(Pattern(
                type="Exercise Benefit",
                frequency="On active days",
                severity="low",
                description=f"Blood pressure is {no_exercise_avg - exercise_avg:.0f} mmHg lower on days with 30+ minutes of exercise"
            ))
    
    # Analyze sleep correlation
    poor_sleep_readings = []
    good_sleep_readings = []
    
    for date, entry in lifestyle_by_date.items():
        if date in readings_by_date:
            sleep = entry.get("sleep_duration") or 7
            day_readings = readings_by_date[date]
            
            if sleep < 6:
                poor_sleep_readings.extend(day_readings)
            elif sleep >= 7:
                good_sleep_readings.extend(day_readings)
    
    if len(poor_sleep_readings) >= 2 and len(good_sleep_readings) >= 2:
        poor_sleep_avg = sum(r["systolic"] for r in poor_sleep_readings) / len(poor_sleep_readings)
        good_sleep_avg = sum(r["systolic"] for r in good_sleep_readings) / len(good_sleep_readings)
        
        if poor_sleep_avg - good_sleep_avg > 8:
            patterns.append(Pattern(
                type="Sleep Impact",
                frequency="After poor sleep",
                severity="moderate",
                description=f"Blood pressure is {poor_sleep_avg - good_sleep_avg:.0f} mmHg higher after nights with less than 6 hours of sleep"
            ))
    
    return patterns


def _analyze_variability_patterns(readings: List[Dict]) -> List[Pattern]:
    """Analyze BP variability patterns."""
    patterns = []
    
    if len(readings) < 7:
        return patterns
    
    systolic_values = [r["systolic"] for r in readings[:14]]
    
    # Calculate standard deviation
    mean = sum(systolic_values) / len(systolic_values)
    variance = sum((x - mean) ** 2 for x in systolic_values) / len(systolic_values)
    std_dev = variance ** 0.5
    
    if std_dev > 15:
        patterns.append(Pattern(
            type="High Variability",
            frequency=f"Std dev: {std_dev:.1f} mmHg",
            severity="high",
            description="Your readings show high variability which may indicate inconsistent measurement technique or underlying issues"
        ))
    elif std_dev < 8:
        patterns.append(Pattern(
            type="Consistent Readings",
            frequency=f"Std dev: {std_dev:.1f} mmHg",
            severity="low",
            description="Your blood pressure readings are consistent, indicating good measurement technique"
        ))
    
    return patterns


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
