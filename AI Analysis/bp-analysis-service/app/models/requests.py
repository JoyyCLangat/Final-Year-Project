# requests.py
"""Request models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TimeRange(BaseModel):
    """Time range for analysis."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AnalysisRequest(BaseModel):
    """Base request for all analysis endpoints."""
    patient_id: str
    time_range: Optional[TimeRange] = None


class ForecastRequest(BaseModel):
    """Request for forecast endpoint."""
    patient_id: str
    metric: str = "systolic"  # "systolic" or "diastolic"
    forecast_days: int = Field(default=30, ge=7, le=90)


# ============================================
# Data models for what Supabase returns
# ============================================

class BloodPressureReading(BaseModel):
    """Blood pressure reading from database."""
    id: str
    patient_id: str
    systolic: int
    diastolic: int
    pulse: Optional[int] = None
    measurement_date: datetime
    status: Optional[str] = None
    time_of_day: Optional[str] = None
    position: Optional[str] = None
    arm: Optional[str] = None
    notes: Optional[str] = None


class Medication(BaseModel):
    """Medication from database."""
    id: str
    patient_id: str
    name: str
    dosage: str
    frequency: str
    active: bool = True
    adherence_rate: Optional[float] = None
    time_of_day: Optional[List[str]] = None


class MedicationLog(BaseModel):
    """Medication log entry."""
    id: str
    medication_id: str
    scheduled_time: datetime
    taken: bool
    taken_time: Optional[datetime] = None
    skipped_reason: Optional[str] = None


class LifestyleEntry(BaseModel):
    """Lifestyle entry from database."""
    id: str
    patient_id: str
    entry_date: str
    physical_activity: Optional[int] = None
    exercise_type: Optional[str] = None
    diet_quality: Optional[str] = None
    salt_intake: Optional[str] = None
    sleep_duration: Optional[float] = None
    sleep_quality: Optional[str] = None
    stress_level: Optional[str] = None
    water_intake: Optional[int] = None
    weight: Optional[float] = None
    alcohol_consumption: Optional[int] = None
    smoking_status: Optional[str] = None
    sodium_mg: Optional[int] = None
    notes: Optional[str] = None


class PatientProfile(BaseModel):
    """Patient profile from database."""
    id: str
    user_id: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    blood_type: Optional[str] = None
    risk_level: str = "low"
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
