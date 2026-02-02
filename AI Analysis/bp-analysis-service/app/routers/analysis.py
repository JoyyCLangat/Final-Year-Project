# analysis.py
"""Analysis API router with all 7 endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from app.models import (
    AnalysisRequest,
    ForecastRequest,
    InsightsResponse,
    RiskAssessment,
    TrendPredictionsResponse,
    HealthScore,
    PatternAnalysis,
    CorrelationAnalysis,
    TimeSeriesForecast,
)
from app.services import (
    generate_insights,
    calculate_risk_assessment,
    calculate_predictions,
    calculate_health_score,
    analyze_patterns,
    analyze_correlations,
    generate_forecast,
)
from app.utils import AnalysisCache
from app.errors import AnalysisError
from app.config import get_settings


router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])


@router.post("/insights", response_model=InsightsResponse)
async def get_insights(request: AnalysisRequest):
    """
    Generate personalized health insights for a patient.
    
    Returns array of insights with type, title, message, and recommendations.
    """
    try:
        settings = get_settings()
        days = settings.default_analysis_days
        
        if request.time_range and request.time_range.start_date and request.time_range.end_date:
            days = (request.time_range.end_date - request.time_range.start_date).days
        
        # Check cache
        cached = AnalysisCache.get(request.patient_id, "insights", days=days)
        if cached:
            return InsightsResponse(insights=cached)
        
        insights = await generate_insights(request.patient_id, days)
        
        # Cache result
        AnalysisCache.set(request.patient_id, "insights", [i.dict() for i in insights], days=days)
        
        return InsightsResponse(insights=insights)
    
    except AnalysisError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk-assessment", response_model=RiskAssessment)
async def get_risk_assessment(request: AnalysisRequest):
    """
    Calculate comprehensive risk assessment for a patient.
    
    Returns overall risk level, score (0-100), risk factors, and recommendations.
    """
    try:
        settings = get_settings()
        days = settings.default_analysis_days
        
        if request.time_range and request.time_range.start_date and request.time_range.end_date:
            days = (request.time_range.end_date - request.time_range.start_date).days
        
        # Check cache
        cached = AnalysisCache.get(request.patient_id, "risk_assessment", days=days)
        if cached:
            return RiskAssessment(**cached)
        
        assessment = await calculate_risk_assessment(request.patient_id, days)
        
        # Cache result
        AnalysisCache.set(request.patient_id, "risk_assessment", assessment.dict(), days=days)
        
        return assessment
    
    except AnalysisError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predictions", response_model=TrendPredictionsResponse)
async def get_predictions(request: AnalysisRequest):
    """
    Calculate trend predictions for blood pressure metrics.
    
    Returns predictions for systolic, diastolic, and pulse with confidence levels.
    """
    try:
        settings = get_settings()
        days = settings.default_analysis_days
        
        if request.time_range and request.time_range.start_date and request.time_range.end_date:
            days = (request.time_range.end_date - request.time_range.start_date).days
        
        # Check cache
        cached = AnalysisCache.get(request.patient_id, "predictions", days=days)
        if cached:
            return TrendPredictionsResponse(predictions=cached)
        
        predictions = await calculate_predictions(request.patient_id, days)
        
        # Cache result
        AnalysisCache.set(request.patient_id, "predictions", [p.dict() for p in predictions], days=days)
        
        return TrendPredictionsResponse(predictions=predictions)
    
    except AnalysisError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health-score", response_model=HealthScore)
async def get_health_score(request: AnalysisRequest):
    """
    Calculate comprehensive health score for a patient.
    
    Returns overall score (0-100), category scores, and improvement areas.
    """
    try:
        settings = get_settings()
        days = settings.default_analysis_days
        
        if request.time_range and request.time_range.start_date and request.time_range.end_date:
            days = (request.time_range.end_date - request.time_range.start_date).days
        
        # Check cache
        cached = AnalysisCache.get(request.patient_id, "health_score", days=days)
        if cached:
            return HealthScore(**cached)
        
        score = await calculate_health_score(request.patient_id, days)
        
        # Cache result
        AnalysisCache.set(request.patient_id, "health_score", score.dict(), days=days)
        
        return score
    
    except AnalysisError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns", response_model=PatternAnalysis)
async def get_patterns(request: AnalysisRequest):
    """
    Analyze blood pressure patterns for a patient.
    
    Returns detected patterns with type, frequency, severity, and description.
    """
    try:
        settings = get_settings()
        days = settings.default_analysis_days
        
        if request.time_range and request.time_range.start_date and request.time_range.end_date:
            days = (request.time_range.end_date - request.time_range.start_date).days
        
        # Check cache
        cached = AnalysisCache.get(request.patient_id, "patterns", days=days)
        if cached:
            return PatternAnalysis(**cached)
        
        analysis = await analyze_patterns(request.patient_id, days)
        
        # Cache result
        AnalysisCache.set(request.patient_id, "patterns", analysis.dict(), days=days)
        
        return analysis
    
    except AnalysisError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/correlations", response_model=CorrelationAnalysis)
async def get_correlations(request: AnalysisRequest):
    """
    Analyze correlations between lifestyle factors and blood pressure.
    
    Returns correlations with strength and direction.
    """
    try:
        settings = get_settings()
        days = settings.default_analysis_days
        
        if request.time_range and request.time_range.start_date and request.time_range.end_date:
            days = (request.time_range.end_date - request.time_range.start_date).days
        
        # Check cache
        cached = AnalysisCache.get(request.patient_id, "correlations", days=days)
        if cached:
            return CorrelationAnalysis(**cached)
        
        analysis = await analyze_correlations(request.patient_id, days)
        
        # Cache result
        AnalysisCache.set(request.patient_id, "correlations", analysis.dict(), days=days)
        
        return analysis
    
    except AnalysisError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forecast", response_model=TimeSeriesForecast)
async def get_forecast(request: ForecastRequest):
    """
    Generate time series forecast for blood pressure.
    
    Returns historical data and forecast with confidence bounds.
    """
    try:
        # Check cache
        cached = AnalysisCache.get(
            request.patient_id, 
            "forecast", 
            metric=request.metric,
            days=request.forecast_days
        )
        if cached:
            return TimeSeriesForecast(**cached)
        
        forecast = await generate_forecast(
            request.patient_id,
            request.metric,
            request.forecast_days
        )
        
        # Cache result
        AnalysisCache.set(
            request.patient_id, 
            "forecast", 
            forecast.dict(),
            metric=request.metric,
            days=request.forecast_days
        )
        
        return forecast
    
    except AnalysisError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Cache Management Endpoints
# ==========================================

@router.post("/invalidate-cache/{patient_id}")
async def invalidate_patient_cache(patient_id: str):
    """Invalidate all cached analysis for a patient."""
    AnalysisCache.invalidate(patient_id)
    return {"message": f"Cache invalidated for patient {patient_id}"}


@router.get("/cache-stats")
async def get_cache_stats():
    """Get cache statistics."""
    return AnalysisCache.stats()
