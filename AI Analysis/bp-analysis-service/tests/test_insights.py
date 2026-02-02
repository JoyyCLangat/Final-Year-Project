# test_insights.py
"""Tests for insights service."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Mock data for testing
MOCK_PATIENT = {
    "id": "test-patient-id",
    "user_id": "test-user-id",
    "risk_level": "medium",
    "medical_history": "Hypertension",
    "users": {"name": "Test Patient", "age": 45}
}

MOCK_READINGS = [
    {
        "id": f"reading-{i}",
        "patient_id": "test-patient-id",
        "systolic": 135 + (i % 10),
        "diastolic": 85 + (i % 5),
        "pulse": 72,
        "measurement_date": (datetime.now() - timedelta(days=i)).isoformat(),
        "time_of_day": "morning" if i % 2 == 0 else "evening",
        "status": "elevated"
    }
    for i in range(30)
]

MOCK_MEDICATIONS = [
    {
        "id": "med-1",
        "patient_id": "test-patient-id",
        "name": "Lisinopril",
        "dosage": "10mg",
        "frequency": "Once daily",
        "active": True,
        "adherence_rate": 92.0
    }
]

MOCK_LIFESTYLE = [
    {
        "id": "lifestyle-1",
        "patient_id": "test-patient-id",
        "entry_date": datetime.now().date().isoformat(),
        "physical_activity": 30,
        "diet_quality": "moderate",
        "salt_intake": "moderate",
        "sleep_duration": 7.0,
        "stress_level": "moderate"
    }
]


class TestInsights:
    """Test cases for insights generation."""
    
    @pytest.mark.asyncio
    @patch('app.services.insights.Database')
    async def test_generate_insights_success(self, mock_db):
        """Test successful insights generation."""
        from app.services.insights import generate_insights
        
        # Setup mocks
        mock_db.fetch_patient.return_value = MOCK_PATIENT
        mock_db.fetch_blood_pressure_readings.return_value = MOCK_READINGS
        mock_db.fetch_medications.return_value = MOCK_MEDICATIONS
        mock_db.fetch_lifestyle_entries.return_value = MOCK_LIFESTYLE
        
        # Call function
        insights = await generate_insights("test-patient-id", days=30)
        
        # Assertions
        assert isinstance(insights, list)
        assert len(insights) > 0
        
        for insight in insights:
            assert insight.id is not None
            assert insight.type in ["success", "warning", "info", "danger"]
            assert insight.title is not None
            assert insight.message is not None
            assert 1 <= insight.priority <= 5
    
    @pytest.mark.asyncio
    @patch('app.services.insights.Database')
    async def test_generate_insights_patient_not_found(self, mock_db):
        """Test insights generation with non-existent patient."""
        from app.services.insights import generate_insights
        from app.errors import PatientNotFoundError
        
        mock_db.fetch_patient.return_value = None
        
        with pytest.raises(PatientNotFoundError):
            await generate_insights("non-existent-patient", days=30)
    
    @pytest.mark.asyncio
    @patch('app.services.insights.Database')
    async def test_generate_insights_insufficient_data(self, mock_db):
        """Test insights generation with insufficient data."""
        from app.services.insights import generate_insights
        
        mock_db.fetch_patient.return_value = MOCK_PATIENT
        mock_db.fetch_blood_pressure_readings.return_value = MOCK_READINGS[:3]  # Only 3 readings
        mock_db.fetch_medications.return_value = []
        mock_db.fetch_lifestyle_entries.return_value = []
        
        insights = await generate_insights("test-patient-id", days=30)
        
        # Should return info insight about needing more data
        assert any(i.type == "info" and "More Data" in i.title for i in insights)
