# test_risk.py
"""Tests for risk assessment service."""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta


MOCK_PATIENT = {
    "id": "test-patient-id",
    "user_id": "test-user-id",
    "risk_level": "medium",
    "medical_history": "Type 2 Diabetes",
    "users": {"name": "Test Patient", "age": 55}
}

MOCK_HIGH_BP_READINGS = [
    {
        "id": f"reading-{i}",
        "patient_id": "test-patient-id",
        "systolic": 155 + (i % 15),
        "diastolic": 95 + (i % 10),
        "pulse": 80,
        "measurement_date": (datetime.now() - timedelta(days=i)).isoformat(),
        "status": "high"
    }
    for i in range(20)
]

MOCK_NORMAL_BP_READINGS = [
    {
        "id": f"reading-{i}",
        "patient_id": "test-patient-id",
        "systolic": 118 + (i % 8),
        "diastolic": 75 + (i % 5),
        "pulse": 70,
        "measurement_date": (datetime.now() - timedelta(days=i)).isoformat(),
        "status": "normal"
    }
    for i in range(20)
]

MOCK_MEDICATIONS_LOW_ADHERENCE = [
    {
        "id": "med-1",
        "name": "Lisinopril",
        "dosage": "10mg",
        "active": True,
        "adherence_rate": 65.0
    }
]


class TestRiskAssessment:
    """Test cases for risk assessment calculation."""
    
    @pytest.mark.asyncio
    @patch('app.services.risk_assessment.Database')
    async def test_high_risk_assessment(self, mock_db):
        """Test risk assessment for high-risk patient."""
        from app.services.risk_assessment import calculate_risk_assessment
        
        mock_db.fetch_patient.return_value = MOCK_PATIENT
        mock_db.fetch_blood_pressure_readings.return_value = MOCK_HIGH_BP_READINGS
        mock_db.fetch_medications.return_value = MOCK_MEDICATIONS_LOW_ADHERENCE
        mock_db.fetch_medication_logs.return_value = []
        mock_db.fetch_lifestyle_entries.return_value = []
        
        assessment = await calculate_risk_assessment("test-patient-id")
        
        assert assessment.overallRisk in ["high", "critical"]
        assert assessment.riskScore >= 50
        assert len(assessment.factors) > 0
        assert len(assessment.recommendations) > 0
    
    @pytest.mark.asyncio
    @patch('app.services.risk_assessment.Database')
    async def test_low_risk_assessment(self, mock_db):
        """Test risk assessment for low-risk patient."""
        from app.services.risk_assessment import calculate_risk_assessment
        
        mock_db.fetch_patient.return_value = {
            **MOCK_PATIENT,
            "medical_history": "",
            "users": {"name": "Test Patient", "age": 35}
        }
        mock_db.fetch_blood_pressure_readings.return_value = MOCK_NORMAL_BP_READINGS
        mock_db.fetch_medications.return_value = [
            {"id": "med-1", "name": "Aspirin", "active": True, "adherence_rate": 98.0}
        ]
        mock_db.fetch_medication_logs.return_value = []
        mock_db.fetch_lifestyle_entries.return_value = [
            {
                "entry_date": datetime.now().date().isoformat(),
                "physical_activity": 45,
                "salt_intake": "low",
                "stress_level": "low",
                "sleep_duration": 8.0
            }
        ]
        
        assessment = await calculate_risk_assessment("test-patient-id")
        
        assert assessment.overallRisk in ["low", "moderate"]
        assert assessment.riskScore < 50
    
    @pytest.mark.asyncio
    @patch('app.services.risk_assessment.Database')
    async def test_risk_factors_included(self, mock_db):
        """Test that all relevant risk factors are included."""
        from app.services.risk_assessment import calculate_risk_assessment
        
        mock_db.fetch_patient.return_value = MOCK_PATIENT
        mock_db.fetch_blood_pressure_readings.return_value = MOCK_HIGH_BP_READINGS
        mock_db.fetch_medications.return_value = MOCK_MEDICATIONS_LOW_ADHERENCE
        mock_db.fetch_medication_logs.return_value = []
        mock_db.fetch_lifestyle_entries.return_value = []
        
        assessment = await calculate_risk_assessment("test-patient-id")
        
        factor_names = [f.name for f in assessment.factors]
        
        # Should include BP-related factor
        assert any("BP" in name or "Blood Pressure" in name or "Elevated" in name 
                  for name in factor_names)
