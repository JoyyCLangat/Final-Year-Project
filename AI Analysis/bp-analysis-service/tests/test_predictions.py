# test_predictions.py
"""Tests for predictions service."""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta


MOCK_PATIENT = {
    "id": "test-patient-id",
    "user_id": "test-user-id",
    "users": {"name": "Test Patient", "age": 45}
}

# Readings showing improvement (decreasing systolic)
MOCK_IMPROVING_READINGS = [
    {
        "id": f"reading-{i}",
        "patient_id": "test-patient-id",
        "systolic": 150 - i,  # Decreasing
        "diastolic": 90 - (i // 2),
        "pulse": 72,
        "measurement_date": (datetime.now() - timedelta(days=29-i)).isoformat(),
        "status": "elevated"
    }
    for i in range(30)
]

# Readings showing worsening (increasing systolic)
MOCK_WORSENING_READINGS = [
    {
        "id": f"reading-{i}",
        "patient_id": "test-patient-id",
        "systolic": 120 + i,  # Increasing
        "diastolic": 75 + (i // 2),
        "pulse": 72,
        "measurement_date": (datetime.now() - timedelta(days=29-i)).isoformat(),
        "status": "elevated"
    }
    for i in range(30)
]


class TestPredictions:
    """Test cases for trend predictions."""
    
    @pytest.mark.asyncio
    @patch('app.services.predictions.Database')
    async def test_improving_trend_prediction(self, mock_db):
        """Test predictions for improving BP trend."""
        from app.services.predictions import calculate_predictions
        
        mock_db.fetch_patient.return_value = MOCK_PATIENT
        mock_db.fetch_blood_pressure_readings.return_value = MOCK_IMPROVING_READINGS
        
        predictions = await calculate_predictions("test-patient-id")
        
        assert len(predictions) >= 2  # At least systolic and diastolic
        
        systolic_pred = next(p for p in predictions if "Systolic" in p.metric)
        assert systolic_pred.trend == "improving"
        assert systolic_pred.predictedValue < systolic_pred.currentValue
        assert 0 <= systolic_pred.confidence <= 100
    
    @pytest.mark.asyncio
    @patch('app.services.predictions.Database')
    async def test_worsening_trend_prediction(self, mock_db):
        """Test predictions for worsening BP trend."""
        from app.services.predictions import calculate_predictions
        
        mock_db.fetch_patient.return_value = MOCK_PATIENT
        mock_db.fetch_blood_pressure_readings.return_value = MOCK_WORSENING_READINGS
        
        predictions = await calculate_predictions("test-patient-id")
        
        systolic_pred = next(p for p in predictions if "Systolic" in p.metric)
        assert systolic_pred.trend == "worsening"
        assert systolic_pred.predictedValue > systolic_pred.currentValue
    
    @pytest.mark.asyncio
    @patch('app.services.predictions.Database')
    async def test_insufficient_data_error(self, mock_db):
        """Test predictions with insufficient data."""
        from app.services.predictions import calculate_predictions
        from app.errors import InsufficientDataError
        
        mock_db.fetch_patient.return_value = MOCK_PATIENT
        mock_db.fetch_blood_pressure_readings.return_value = MOCK_IMPROVING_READINGS[:3]
        
        with pytest.raises(InsufficientDataError):
            await calculate_predictions("test-patient-id")
    
    @pytest.mark.asyncio
    @patch('app.services.predictions.Database')
    async def test_prediction_confidence_range(self, mock_db):
        """Test that confidence values are within valid range."""
        from app.services.predictions import calculate_predictions
        
        mock_db.fetch_patient.return_value = MOCK_PATIENT
        mock_db.fetch_blood_pressure_readings.return_value = MOCK_IMPROVING_READINGS
        
        predictions = await calculate_predictions("test-patient-id")
        
        for pred in predictions:
            assert 0 <= pred.confidence <= 100
            assert pred.timeframe == "30 days"
