# config.py
"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Cache
    cache_ttl: int = 1800  # 30 minutes
    cache_max_size: int = 100
    
    # Analysis
    min_readings_for_analysis: int = 7
    default_analysis_days: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
