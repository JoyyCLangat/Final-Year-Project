# risk_assessment.py
"""Risk assessment analysis service."""

from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.models import RiskAssessment, RiskFactor
from app.utils import Database
from app.errors import InsufficientDataError, PatientNotFoundError
from app.config import get_settings


async def calculate_risk_assessment(patient_id: str, days: int = 30) -> RiskAssessment:
    """
    Calculate comprehensive risk assessment for a patient.
    
    Returns RiskAssessment matching frontend interface:
    - overallRisk: 'low' | 'moderate' | 'high' | 'critical'
    - riskScore: number (0-100)
    - factors: Array of {name, impact, description}
    - recommendations: string[]
    """
    settings = get_settings()
    
    # Fetch patient data
    patient = Database.fetch_patient(patient_id)
    if not patient:
        raise PatientNotFoundError(patient_id)
    
    readings = Database.fetch_blood_pressure_readings(patient_id, days)
    medications = Database.fetch_medications(patient_id)
    medication_logs = Database.fetch_medication_logs(patient_id, days)
    lifestyle = Database.fetch_lifestyle_entries(patient_id, days)
    
    risk_score = 0
    factors: List[RiskFactor] = []
    recommendations: List[str] = []
    
    # ==========================================
    # 1. Blood Pressure Analysis (0-35 points)
    # ==========================================
    if readings:
        recent_readings = readings[:14]
        avg_systolic = sum(r["systolic"] for r in recent_readings) / len(recent_readings)
        avg_diastolic = sum(r["diastolic"] for r in recent_readings) / len(recent_readings)
        
        # High readings count
        high_count = sum(1 for r in recent_readings if r["systolic"] >= 140 or r["diastolic"] >= 90)
        critical_count = sum(1 for r in recent_readings if r["systolic"] >= 180 or r["diastolic"] >= 120)
        
        # Critical episodes
        if critical_count > 0:
            risk_score += 25
            factors.append(RiskFactor(
                name="Critical BP Episodes",
                impact="high",
                description=f"{critical_count} reading(s) in hypertensive crisis range"
            ))
            recommendations.append("Seek immediate medical evaluation for critical readings")
        
        # Consistently high
        high_percentage = (high_count / len(recent_readings)) * 100 if recent_readings else 0
        if high_percentage >= 70:
            risk_score += 20
            factors.append(RiskFactor(
                name="Consistently Elevated BP",
                impact="high",
                description=f"{high_percentage:.0f}% of readings are elevated"
            ))
            recommendations.append("Review current medication effectiveness with provider")
        elif high_percentage >= 40:
            risk_score += 12
            factors.append(RiskFactor(
                name="Frequently Elevated BP",
                impact="moderate",
                description=f"{high_percentage:.0f}% of readings are elevated"
            ))
            recommendations.append("Monitor blood pressure more frequently")
        elif high_percentage >= 20:
            risk_score += 5
            factors.append(RiskFactor(
                name="Occasionally Elevated BP",
                impact="low",
                description=f"{high_percentage:.0f}% of readings are elevated"
            ))
        
        # Average BP level
        if avg_systolic >= 160 or avg_diastolic >= 100:
            risk_score += 10
        elif avg_systolic >= 140 or avg_diastolic >= 90:
            risk_score += 6
        elif avg_systolic >= 130 or avg_diastolic >= 85:
            risk_score += 3
        
        # BP Variability
        systolic_values = [r["systolic"] for r in recent_readings]
        variability = max(systolic_values) - min(systolic_values) if systolic_values else 0
        if variability > 40:
            risk_score += 8
            factors.append(RiskFactor(
                name="Blood Pressure Variability",
                impact="high",
                description=f"Readings vary by {variability} mmHg between measurements"
            ))
            recommendations.append("Maintain consistent measurement times and conditions")
        elif variability > 25:
            risk_score += 4
            factors.append(RiskFactor(
                name="Blood Pressure Variability",
                impact="moderate",
                description=f"Readings vary by {variability} mmHg between measurements"
            ))
    else:
        risk_score += 10
        factors.append(RiskFactor(
            name="Insufficient BP Data",
            impact="moderate",
            description="No recent blood pressure readings available"
        ))
        recommendations.append("Start monitoring blood pressure daily")
    
    # ==========================================
    # 2. Medication Adherence (0-20 points)
    # ==========================================
    if medications:
        active_meds = [m for m in medications if m.get("active", True)]
        if active_meds:
            adherence_rates = [m.get("adherence_rate") or 100 for m in active_meds]
            avg_adherence = sum(adherence_rates) / len(adherence_rates)
            
            if avg_adherence < 70:
                risk_score += 20
                factors.append(RiskFactor(
                    name="Poor Medication Adherence",
                    impact="high",
                    description=f"Average adherence rate is {avg_adherence:.0f}%"
                ))
                recommendations.append("Set up medication reminders and discuss barriers with your doctor")
            elif avg_adherence < 85:
                risk_score += 12
                factors.append(RiskFactor(
                    name="Medication Adherence",
                    impact="moderate",
                    description=f"Missed doses detected (adherence: {avg_adherence:.0f}%)"
                ))
                recommendations.append("Use a pill organizer or reminder app")
            elif avg_adherence >= 95:
                factors.append(RiskFactor(
                    name="Medication Adherence",
                    impact="low",
                    description=f"Excellent adherence rate ({avg_adherence:.0f}%)"
                ))
    
    # ==========================================
    # 3. Lifestyle Factors (0-25 points)
    # ==========================================
    if lifestyle:
        recent_lifestyle = lifestyle[0]
        
        # Salt intake
        if recent_lifestyle.get("salt_intake") == "high":
            risk_score += 8
            factors.append(RiskFactor(
                name="High Sodium Diet",
                impact="high",
                description="Reported high salt intake increases BP"
            ))
            recommendations.append("Reduce sodium intake to less than 2,300mg daily")
        elif recent_lifestyle.get("salt_intake") == "moderate":
            risk_score += 3
        
        # Physical activity
        activity = recent_lifestyle.get("physical_activity") or 0
        if activity < 15:
            risk_score += 8
            factors.append(RiskFactor(
                name="Low Physical Activity",
                impact="high",
                description=f"Only {activity} minutes of activity logged"
            ))
            recommendations.append("Aim for 30 minutes of moderate exercise 5 days a week")
        elif activity < 30:
            risk_score += 4
            factors.append(RiskFactor(
                name="Physical Activity",
                impact="moderate",
                description=f"{activity} minutes of activity - could be increased"
            ))
        
        # Stress level
        stress = recent_lifestyle.get("stress_level")
        if stress == "severe":
            risk_score += 8
            factors.append(RiskFactor(
                name="Severe Stress",
                impact="high",
                description="High stress levels can significantly elevate BP"
            ))
            recommendations.append("Practice stress management: meditation, deep breathing, or yoga")
        elif stress == "high":
            risk_score += 5
            factors.append(RiskFactor(
                name="High Stress",
                impact="moderate",
                description="Stress can contribute to elevated blood pressure"
            ))
        
        # Sleep
        sleep = recent_lifestyle.get("sleep_duration") or 7
        if sleep < 5:
            risk_score += 6
            factors.append(RiskFactor(
                name="Sleep Deprivation",
                impact="high",
                description=f"Only {sleep:.1f} hours of sleep"
            ))
            recommendations.append("Prioritize getting 7-9 hours of quality sleep")
        elif sleep < 6:
            risk_score += 3
            factors.append(RiskFactor(
                name="Insufficient Sleep",
                impact="moderate",
                description=f"{sleep:.1f} hours of sleep - below recommended"
            ))
        
        # Alcohol
        alcohol = recent_lifestyle.get("alcohol_consumption") or 0
        if alcohol > 2:
            risk_score += 5
            factors.append(RiskFactor(
                name="Alcohol Consumption",
                impact="moderate",
                description=f"{alcohol} drinks - above recommended limit"
            ))
            recommendations.append("Limit alcohol to 1-2 drinks per day maximum")
        
        # Smoking
        if recent_lifestyle.get("smoking_status") == "current":
            risk_score += 10
            factors.append(RiskFactor(
                name="Smoking",
                impact="high",
                description="Smoking significantly increases cardiovascular risk"
            ))
            recommendations.append("Consider smoking cessation programs")
    
    # ==========================================
    # 4. Patient Demographics (0-15 points)
    # ==========================================
    age = patient.get("users", {}).get("age") or 0
    if age >= 65:
        risk_score += 10
        factors.append(RiskFactor(
            name="Age",
            impact="moderate",
            description=f"Age {age} is a non-modifiable risk factor"
        ))
    elif age >= 55:
        risk_score += 6
    elif age >= 45:
        risk_score += 3
    
    # Medical history
    medical_history = (patient.get("medical_history") or "").lower()
    if "diabetes" in medical_history:
        risk_score += 10
        factors.append(RiskFactor(
            name="Diabetes",
            impact="high",
            description="Diabetes increases cardiovascular risk"
        ))
        recommendations.append("Maintain good blood sugar control")
    
    if "kidney" in medical_history or "renal" in medical_history:
        risk_score += 10
        factors.append(RiskFactor(
            name="Kidney Disease",
            impact="high",
            description="Kidney function affects blood pressure regulation"
        ))
    
    if "heart" in medical_history or "cardiac" in medical_history:
        risk_score += 8
        factors.append(RiskFactor(
            name="Heart Condition",
            impact="high",
            description="Existing heart condition increases risk"
        ))
    
    # ==========================================
    # Calculate Overall Risk Level
    # ==========================================
    risk_score = min(100, risk_score)  # Cap at 100
    
    if risk_score >= 70:
        overall_risk = "critical"
        recommendations.insert(0, "Schedule urgent appointment with your healthcare provider")
    elif risk_score >= 50:
        overall_risk = "high"
        recommendations.insert(0, "Schedule follow-up appointment within 1-2 weeks")
    elif risk_score >= 30:
        overall_risk = "moderate"
        recommendations.insert(0, "Continue regular monitoring and follow treatment plan")
    else:
        overall_risk = "low"
        recommendations.insert(0, "Maintain your healthy lifestyle habits")
    
    # Limit recommendations to top 5
    recommendations = recommendations[:5]
    
    return RiskAssessment(
        overallRisk=overall_risk,
        riskScore=risk_score,
        factors=factors,
        recommendations=recommendations
    )
