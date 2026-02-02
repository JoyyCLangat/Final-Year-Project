# insights.py
"""Insights generation service."""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid

from app.models import Insight
from app.utils import Database
from app.errors import InsufficientDataError, PatientNotFoundError
from app.config import get_settings


async def generate_insights(patient_id: str, days: int = 30) -> List[Insight]:
    """
    Generate personalized health insights for a patient.
    
    Returns insights matching the frontend Insight interface:
    - id: string
    - type: 'success' | 'warning' | 'info' | 'danger'
    - title: string
    - message: string
    - priority: number (1-5)
    - timestamp: ISO date string
    - recommendations?: string[]
    """
    settings = get_settings()
    
    # Fetch patient data
    patient = Database.fetch_patient(patient_id)
    if not patient:
        raise PatientNotFoundError(patient_id)
    
    readings = Database.fetch_blood_pressure_readings(patient_id, days)
    medications = Database.fetch_medications(patient_id)
    lifestyle = Database.fetch_lifestyle_entries(patient_id, days)
    
    insights: List[Insight] = []
    now = datetime.now().isoformat() + "Z"
    
    # Check if enough data
    if len(readings) < settings.min_readings_for_analysis:
        insights.append(Insight(
            id=str(uuid.uuid4()),
            type="info",
            title="More Data Needed",
            message=f"You have {len(readings)} readings. We need at least {settings.min_readings_for_analysis} for detailed analysis.",
            priority=3,
            timestamp=now,
            recommendations=["Take your blood pressure daily", "Log readings at consistent times"]
        ))
        return insights
    
    # Analyze BP trends
    insights.extend(_analyze_bp_patterns(readings, now))
    
    # Analyze medication adherence
    if medications:
        insights.extend(_analyze_medication_adherence(medications, now))
    
    # Analyze lifestyle factors
    if lifestyle:
        insights.extend(_analyze_lifestyle(lifestyle, now))
    
    # Analyze time-of-day patterns
    insights.extend(_analyze_time_patterns(readings, now))
    
    # Sort by priority
    insights.sort(key=lambda x: x.priority)
    
    return insights[:8]  # Return top 8 insights


def _analyze_bp_patterns(readings: List[Dict], timestamp: str) -> List[Insight]:
    """Analyze blood pressure patterns."""
    insights = []
    
    if not readings:
        return insights
    
    # Calculate averages
    recent_readings = readings[:14]  # Last 2 weeks
    older_readings = readings[14:28] if len(readings) > 14 else []
    
    avg_systolic = sum(r["systolic"] for r in recent_readings) / len(recent_readings)
    avg_diastolic = sum(r["diastolic"] for r in recent_readings) / len(recent_readings)
    
    # Check for improvement
    if older_readings:
        old_avg_sys = sum(r["systolic"] for r in older_readings) / len(older_readings)
        if avg_systolic < old_avg_sys - 5:
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="success",
                title="Blood Pressure Improving",
                message=f"Your average systolic BP has decreased by {old_avg_sys - avg_systolic:.0f} mmHg compared to the previous period.",
                priority=1,
                timestamp=timestamp,
                recommendations=["Keep up your current routine", "Continue monitoring regularly"]
            ))
        elif avg_systolic > old_avg_sys + 5:
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="warning",
                title="Blood Pressure Trending Up",
                message=f"Your average systolic BP has increased by {avg_systolic - old_avg_sys:.0f} mmHg. Consider reviewing your lifestyle factors.",
                priority=2,
                timestamp=timestamp,
                recommendations=[
                    "Review your sodium intake",
                    "Ensure medication compliance",
                    "Consider scheduling a check-up"
                ]
            ))
    
    # Check for high readings
    high_count = sum(1 for r in recent_readings if r["systolic"] >= 140 or r["diastolic"] >= 90)
    if high_count > len(recent_readings) * 0.5:
        insights.append(Insight(
            id=str(uuid.uuid4()),
            type="danger",
            title="Consistently Elevated Readings",
            message=f"{high_count} out of {len(recent_readings)} recent readings are elevated. Please consult your healthcare provider.",
            priority=1,
            timestamp=timestamp,
            recommendations=[
                "Contact your doctor",
                "Review your medication",
                "Monitor more frequently"
            ]
        ))
    
    # Check for critical readings
    critical_count = sum(1 for r in recent_readings if r["systolic"] >= 180 or r["diastolic"] >= 120)
    if critical_count > 0:
        insights.append(Insight(
            id=str(uuid.uuid4()),
            type="danger",
            title="Critical Reading Detected",
            message=f"You had {critical_count} reading(s) in the critical range. Seek medical attention if symptoms occur.",
            priority=1,
            timestamp=timestamp,
            recommendations=[
                "Seek immediate medical attention if experiencing symptoms",
                "Contact your healthcare provider today",
                "Do not skip medications"
            ]
        ))
    
    # Check for good control
    normal_count = sum(1 for r in recent_readings if r["systolic"] < 130 and r["diastolic"] < 85)
    if normal_count >= len(recent_readings) * 0.7:
        insights.append(Insight(
            id=str(uuid.uuid4()),
            type="success",
            title="Excellent BP Control",
            message=f"{normal_count} out of {len(recent_readings)} readings are within normal range. Great job!",
            priority=2,
            timestamp=timestamp,
            recommendations=["Maintain your current lifestyle", "Continue regular monitoring"]
        ))
    
    # Check variability
    systolic_values = [r["systolic"] for r in recent_readings]
    if max(systolic_values) - min(systolic_values) > 30:
        insights.append(Insight(
            id=str(uuid.uuid4()),
            type="warning",
            title="High BP Variability",
            message="Your blood pressure readings show significant variability. Consistent readings are important for accurate assessment.",
            priority=3,
            timestamp=timestamp,
            recommendations=[
                "Take readings at the same time daily",
                "Rest for 5 minutes before measuring",
                "Use the same arm each time"
            ]
        ))
    
    return insights


def _analyze_medication_adherence(medications: List[Dict], timestamp: str) -> List[Insight]:
    """Analyze medication adherence."""
    insights = []
    
    active_meds = [m for m in medications if m.get("active", True)]
    if not active_meds:
        return insights
    
    # Check adherence rates
    low_adherence_meds = [m for m in active_meds if (m.get("adherence_rate") or 100) < 85]
    high_adherence_meds = [m for m in active_meds if (m.get("adherence_rate") or 0) >= 95]
    
    if low_adherence_meds:
        med_names = ", ".join(m["name"] for m in low_adherence_meds[:2])
        insights.append(Insight(
            id=str(uuid.uuid4()),
            type="warning",
            title="Medication Adherence Alert",
            message=f"Your adherence to {med_names} could be improved. Consistent medication use is key to BP control.",
            priority=2,
            timestamp=timestamp,
            recommendations=[
                "Set daily medication reminders",
                "Use a pill organizer",
                "Talk to your doctor if side effects are an issue"
            ]
        ))
    
    if len(high_adherence_meds) == len(active_meds) and active_meds:
        insights.append(Insight(
            id=str(uuid.uuid4()),
            type="success",
            title="Excellent Medication Adherence",
            message="You're taking your medications consistently. This significantly helps control your blood pressure.",
            priority=3,
            timestamp=timestamp
        ))
    
    return insights


def _analyze_lifestyle(lifestyle: List[Dict], timestamp: str) -> List[Insight]:
    """Analyze lifestyle factors."""
    insights = []
    
    if not lifestyle:
        return insights
    
    recent = lifestyle[0]  # Most recent entry
    
    # Exercise analysis
    activity = recent.get("physical_activity") or 0
    if activity >= 30:
        insights.append(Insight(
            id=str(uuid.uuid4()),
            type="success",
            title="Great Exercise Habits",
            message=f"You logged {activity} minutes of activity. Regular exercise helps lower BP naturally.",
            priority=4,
            timestamp=timestamp
        ))
    elif activity < 15:
        insights.append(Insight(
            id=str(uuid.uuid4()),
            type="info",
            title="Increase Physical Activity",
            message="Consider adding more physical activity to your routine. Even a 30-minute walk can help.",
            priority=3,
            timestamp=timestamp,
            recommendations=[
                "Aim for 30 minutes of moderate exercise daily",
                "Start with walking",
                "Take the stairs when possible"
            ]
        ))
    
    # Salt intake
    if recent.get("salt_intake") == "high":
        insights.append(Insight(
            id=str(uuid.uuid4()),
            type="warning",
            title="High Sodium Intake",
            message="High sodium intake can elevate blood pressure. Try to reduce salt in your diet.",
            priority=2,
            timestamp=timestamp,
            recommendations=[
                "Avoid processed foods",
                "Don't add salt at the table",
                "Read nutrition labels"
            ]
        ))
    
    # Sleep
    sleep = recent.get("sleep_duration") or 7
    if sleep < 6:
        insights.append(Insight(
            id=str(uuid.uuid4()),
            type="warning",
            title="Insufficient Sleep",
            message=f"You're getting {sleep:.1f} hours of sleep. Poor sleep can affect blood pressure.",
            priority=3,
            timestamp=timestamp,
            recommendations=[
                "Aim for 7-9 hours of sleep",
                "Maintain a consistent sleep schedule",
                "Limit screen time before bed"
            ]
        ))
    
    # Stress
    if recent.get("stress_level") in ["high", "severe"]:
        insights.append(Insight(
            id=str(uuid.uuid4()),
            type="warning",
            title="High Stress Levels",
            message="Chronic stress can elevate blood pressure. Consider stress management techniques.",
            priority=3,
            timestamp=timestamp,
            recommendations=[
                "Practice deep breathing exercises",
                "Try meditation or yoga",
                "Take regular breaks during work"
            ]
        ))
    
    return insights


def _analyze_time_patterns(readings: List[Dict], timestamp: str) -> List[Insight]:
    """Analyze time-of-day patterns."""
    insights = []
    
    if len(readings) < 7:
        return insights
    
    # Group by time of day
    morning = [r for r in readings if r.get("time_of_day") == "morning"]
    evening = [r for r in readings if r.get("time_of_day") in ["evening", "night"]]
    
    if len(morning) >= 3 and len(evening) >= 3:
        morning_avg = sum(r["systolic"] for r in morning) / len(morning)
        evening_avg = sum(r["systolic"] for r in evening) / len(evening)
        
        if morning_avg - evening_avg > 15:
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="info",
                title="Morning Blood Pressure Surge",
                message=f"Your morning readings average {morning_avg:.0f} mmHg vs {evening_avg:.0f} mmHg in the evening. Morning surges are common but worth monitoring.",
                priority=3,
                timestamp=timestamp,
                recommendations=[
                    "Take morning medications before getting out of bed",
                    "Rise slowly in the morning",
                    "Discuss with your doctor if pattern persists"
                ]
            ))
        elif evening_avg - morning_avg > 15:
            insights.append(Insight(
                id=str(uuid.uuid4()),
                type="warning",
                title="Elevated Evening Readings",
                message=f"Your blood pressure tends to spike in the evening hours ({evening_avg:.0f} mmHg vs {morning_avg:.0f} mmHg in the morning).",
                priority=2,
                timestamp=timestamp,
                recommendations=[
                    "Reduce salt intake after 6 PM",
                    "Practice relaxation techniques before bed",
                    "Avoid caffeine in the afternoon"
                ]
            ))
    
    return insights
