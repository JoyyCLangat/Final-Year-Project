# main.py
"""FastAPI application entry point."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import analysis_router
from app.errors import AnalysisError, analysis_error_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    settings = get_settings()
    print(f"Starting BP Analysis Service...")
    print(f"Debug mode: {settings.debug}")
    yield
    # Shutdown
    print("Shutting down BP Analysis Service...")


# Create FastAPI app
app = FastAPI(
    title="BP Smart Analysis API",
    description="Intelligent blood pressure analysis and health insights service",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
@app.exception_handler(AnalysisError)
async def handle_analysis_error(request: Request, exc: AnalysisError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


# Include routers
app.include_router(analysis_router)


# Root endpoint
@app.get("/")
async def root():
    """API information."""
    return {
        "name": "BP Smart Analysis API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "insights": "POST /api/v1/analysis/insights",
            "risk_assessment": "POST /api/v1/analysis/risk-assessment",
            "predictions": "POST /api/v1/analysis/predictions",
            "health_score": "POST /api/v1/analysis/health-score",
            "patterns": "POST /api/v1/analysis/patterns",
            "correlations": "POST /api/v1/analysis/correlations",
            "forecast": "POST /api/v1/analysis/forecast",
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "bp-analysis-service"
    }


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
