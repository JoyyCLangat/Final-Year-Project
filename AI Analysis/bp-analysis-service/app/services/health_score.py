# health_score.py
"""Health score calculation service."""

from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.models import HealthScore, HealthCategory
from app.utils import Database
from app.errors import InsufficientDataError, PatientNotFoundError
from app.config import get_settings


async def calculate_health_score(patient_id: str, days: int = 30) -> HealthScore:
    """
    Calculate comprehensive health score for a patient.
    
    Returns HealthScore matching frontend interface:
    - overall: number (0-100)
    - categories: Array of {name, score, status}
    - improvementAreas: string[]
    """
    settings = get_settings()
    
    # Fetch patient data
    patient = Database.fetch_patient(patient_id)
    if not patient:
        raise PatientNotFoundError(patient_id)
    
    readings = Database.fetch_blood_pressure_readings(patient_id, days)
    medications = Database.fetch_medications(patient_id)
    lifestyle = Database.fetch_lifestyle_entries(patient_id, days)
    
    categories: List[HealthCategory] = []
    improvement_areas: List[str] = []
    
    # ==========================================
    # 1. Blood Pressure Control Score
    # ==========================================
    bp_score = _calculate_bp_score(readings)
    bp_status = _score_to_status(bp_score)
    categories.append(HealthCategory(
        name="Blood Pressure Control",
        score=bp_score,
        status=bp_status
    ))
    
    if bp_score < 70:
        improvement_areas.append("Focus on consistent blood pressure management")
    if bp_score < 50:
        improvement_areas.append("Consult your doctor about adjusting treatment")
    
    # ==========================================
    # 2. Medication Adherence Score
    # ==========================================
    med_score = _calculate_medication_score(medications)
    med_status = _score_to_status(med_score)
    categories.append(HealthCategory(
        name="Medication Adherence",
        score=med_score,
        status=med_status
    ))
    
    if med_score < 85:
        improvement_areas.append("Set reminders to improve medication consistency")
    
    # ==========================================
    # 3. Lifestyle Factors Score
    # ==========================================
    lifestyle_score = _calculate_lifestyle_score(lifestyle)
    lifestyle_status = _score_to_status(lifestyle_score)
    categories.append(HealthCategory(
        name="Lifestyle Factors",
        score=lifestyle_score,
        status=lifestyle_status
    ))
    
    if lifestyle_score < 70:
        improvement_areas.append("Increase physical activity to 150 min/week")
    if lifestyle_score < 60:
        improvement_areas.append("Reduce sodium intake below 2000mg/day")
    
    # ==========================================
    # 4. Monitoring Consistency Score
    # ==========================================
    monitoring_score = _calculate_monitoring_score(readings, days)
    monitoring_status = _score_to_status(monitoring_score)
    categories.append(HealthCategory(
        name="Monitoring Consistency",
        score=monitoring_score,
        status=monitoring_status
    ))
    
    if monitoring_score < 70:
        improvement_areas.append("Monitor blood pressure more regularly")
    
    # ==========================================
    # 5. Sleep & Recovery Score (if data available)
    # ==========================================
    if lifestyle:
        sleep_score = _calculate_sleep_score(lifestyle)
        sleep_status = _score_to_status(sleep_score)
        categories.append(HealthCategory(
            name="Sleep & Recovery",
            score=sleep_score,
            status=sleep_status
        ))
        
        if sleep_score < 70:
            improvement_areas.append("Improve sleep quality and duration")
    
    # ==========================================
    # Calculate Overall Score
    # ==========================================
    # Weighted average: BP control is most important
    weights = {
        "Blood Pressure Control": 0.35,
        "Medication Adherence": 0.25,
        "Lifestyle Factors": 0.20,
        "Monitoring Consistency": 0.10,
        "Sleep & Recovery": 0.10,
    }
    
    total_weight = sum(weights.get(c.name, 0.1) for c in categories)
    overall = sum(
        c.score * weights.get(c.name, 0.1) 
        for c in categories
    ) / total_weight
    
    overall = round(overall)
    
    # Limit improvement areas to top 5
    improvement_areas = improvement_areas[:5]
    
    return HealthScore(
        overall=overall,
        categories=categories,
        improvementAreas=improvement_areas
    )


def _calculate_bp_score(readings: List[Dict]) -> int:
    """Calculate blood pressure control score (0-100)."""
    if not readings:
        return 50  # Neutral score for no data
    
    recent = readings[:14]  # Last 2 weeks
    
    # Count readings in each category
    normal = 0
    elevated = 0
    high = 0
    critical = 0
    
    for r in recent:
        sys = r["systolic"]
        dia = r["diastolic"]
        
        if sys >= 180 or dia >= 120:
            critical += 1
        elif sys >= 140 or dia >= 90:
            high += 1
        elif sys >= 130 or dia >= 85:
            elevated += 1
        else:
            normal += 1
    
    total = len(recent)
    
    # Calculate score based on distribution
    # Normal readings = full points, elevated = partial, high/critical = low/zero
    score = (
        (normal / total) * 100 +
        (elevated / total) * 60 +
        (high / total) * 30 +
        (critical / total) * 0
    )
    
    # Bonus for consistency (low variability)
    systolic_values = [r["systolic"] for r in recent]
    if systolic_values:
        variability = max(systolic_values) - min(systolic_values)
        if variability < 15:
            score += 5  # Bonus for consistent readings
        elif variability > 30:
            score -= 10  # Penalty for high variability
    
    return max(0, min(100, round(score)))


def _calculate_medication_score(medications: List[Dict]) -> int:
    """Calculate medication adherence score (0-100)."""
    if not medications:
        return 85  # Default good score if no medications prescribed
    
    active_meds = [m for m in medications if m.get("active", True)]
    
    if not active_meds:
        return 85
    
    # Average adherence rate
    adherence_rates = []
    for med in active_meds:
        rate = med.get("adherence_rate")
        if rate is not None:
            adherence_rates.append(rate)
    
    if not adherence_rates:
        return 75  # Default moderate score if no adherence data
    
    avg_adherence = sum(adherence_rates) / len(adherence_rates)
    
    return max(0, min(100, round(avg_adherence)))


def _calculate_lifestyle_score(lifestyle: List[Dict]) -> int:
    """Calculate lifestyle factors score (0-100)."""
    if not lifestyle:
        return 50  # Neutral score for no data
    
    scores = []
    
    for entry in lifestyle[:7]:  # Last 7 days
        day_score = 50  # Base score
        
        # Physical activity (up to +20)
        activity = entry.get("physical_activity") or 0
        if activity >= 30:
            day_score += 20
        elif activity >= 15:
            day_score += 10
        elif activity > 0:
            day_score += 5
        
        # Diet quality (up to +15)
        diet = entry.get("diet_quality")
        if diet == "healthy":
            day_score += 15
        elif diet == "moderate":
            day_score += 8
        
        # Salt intake (up to +10)
        salt = entry.get("salt_intake")
        if salt == "low":
            day_score += 10
        elif salt == "moderate":
            day_score += 5
        elif salt == "high":
            day_score -= 5
        
        # Stress level (up to +10)
        stress = entry.get("stress_level")
        if stress == "low":
            day_score += 10
        elif stress == "moderate":
            day_score += 5
        elif stress in ["high", "severe"]:
            day_score -= 5
        
        # Water intake (up to +5)
        water = entry.get("water_intake") or 0
        if water >= 8:
            day_score += 5
        elif water >= 6:
            day_score += 3
        
        scores.append(min(100, day_score))
    
    return round(sum(scores) / len(scores)) if scores else 50


def _calculate_monitoring_score(readings: List[Dict], days: int) -> int:
    """Calculate monitoring consistency score (0-100)."""
    if not readings:
        return 0
    
    # Expected: at least 1 reading per day
    expected_readings = days
    actual_readings = len(readings)
    
    # Calculate percentage of expected readings
    coverage = (actual_readings / expected_readings) * 100
    
    # Bonus for consistent timing
    times = [r.get("time_of_day") for r in readings if r.get("time_of_day")]
    if times:
        most_common = max(set(times), key=times.count)
        consistency = times.count(most_common) / len(times)
        coverage += consistency * 10  # Bonus for consistent timing
    
    return max(0, min(100, round(coverage)))


def _calculate_sleep_score(lifestyle: List[Dict]) -> int:
    """Calculate sleep quality score (0-100)."""
    if not lifestyle:
        return 50
    
    scores = []
    
    for entry in lifestyle[:7]:
        day_score = 50
        
        # Sleep duration (up to +30)
        duration = entry.get("sleep_duration") or 7
        if 7 <= duration <= 9:
            day_score += 30
        elif 6 <= duration < 7 or 9 < duration <= 10:
            day_score += 20
        elif 5 <= duration < 6:
            day_score += 10
        
        # Sleep quality (up to +20)
        quality = entry.get("sleep_quality")
        if quality == "excellent":
            day_score += 20
        elif quality == "good":
            day_score += 15
        elif quality == "fair":
            day_score += 8
        
        scores.append(min(100, day_score))
    
    return round(sum(scores) / len(scores)) if scores else 50


def _score_to_status(score: int) -> str:
    """Convert numeric score to status label."""
    if score >= 85:
        return "excellent"
    elif score >= 70:
        return "good"
    elif score >= 50:
        return "fair"
    else:
        return "poor"
