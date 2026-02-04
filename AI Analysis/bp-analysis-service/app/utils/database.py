# database.py
"""Supabase database connection and data fetching utilities."""

from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os

from app.config import get_settings


class Database:
    """Database connection and query handler."""
    
    _client: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client."""
        if cls._client is None:
            settings = get_settings()
            
            # Debug: print connection info
            print(f"Connecting to Supabase: {settings.supabase_url[:30]}...")
            
            if not settings.supabase_url or not settings.supabase_service_key:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
            
            cls._client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return cls._client
    
    @classmethod
    def fetch_patient(cls, patient_id: str) -> Optional[Dict[str, Any]]:
        """Fetch patient profile."""
        try:
            client = cls.get_client()
            
            # First try to get patient with user join
            result = client.table("patients").select(
                "*, users(name, email, age)"
            ).eq("id", patient_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            # If not found by patient id, try by user_id
            result = client.table("patients").select(
                "*, users(name, email, age)"
            ).eq("user_id", patient_id).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            return None
        except Exception as e:
            print(f"Error fetching patient: {e}")
            raise
    
    @classmethod
    def fetch_blood_pressure_readings(
        cls,
        patient_id: str,
        days: int = 30,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Fetch blood pressure readings for a patient."""
        client = cls.get_client()
        
        # Calculate date range
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=days)
        
        result = client.table("blood_pressure_readings").select("*").eq(
            "patient_id", patient_id
        ).gte(
            "measurement_date", start_date.isoformat()
        ).lte(
            "measurement_date", end_date.isoformat()
        ).order(
            "measurement_date", desc=True
        ).execute()
        
        return result.data or []
    
    @classmethod
    def fetch_medications(
        cls,
        patient_id: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Fetch medications for a patient."""
        client = cls.get_client()
        
        query = client.table("medications").select("*").eq("patient_id", patient_id)
        
        if active_only:
            query = query.eq("active", True)
        
        result = query.execute()
        return result.data or []
    
    @classmethod
    def fetch_medication_logs(
        cls,
        patient_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Fetch medication logs for a patient."""
        client = cls.get_client()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        result = client.table("medication_logs").select("*").eq(
            "patient_id", patient_id
        ).gte(
            "scheduled_time", cutoff_date.isoformat()
        ).order(
            "scheduled_time", desc=True
        ).execute()
        
        return result.data or []
    
    @classmethod
    def fetch_lifestyle_entries(
        cls,
        patient_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Fetch lifestyle entries for a patient."""
        client = cls.get_client()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        
        result = client.table("lifestyle_entries").select("*").eq(
            "patient_id", patient_id
        ).gte(
            "entry_date", cutoff_date.isoformat()
        ).order(
            "entry_date", desc=True
        ).execute()
        
        return result.data or []
    
    @classmethod
    def fetch_all_patient_data(
        cls,
        patient_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Fetch all data needed for analysis."""
        return {
            "patient": cls.fetch_patient(patient_id),
            "readings": cls.fetch_blood_pressure_readings(patient_id, days),
            "medications": cls.fetch_medications(patient_id),
            "medication_logs": cls.fetch_medication_logs(patient_id, days),
            "lifestyle": cls.fetch_lifestyle_entries(patient_id, days),
        }


# Convenience function
def get_database() -> Database:
    """Get database instance."""
    return Database()