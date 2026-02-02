# BP Smart Analysis Service

A Python FastAPI service providing intelligent blood pressure analysis, risk assessment, and health insights.

## Features

- **7 Analysis Endpoints** matching your frontend interfaces exactly
- **Caching** for improved performance
- **Supabase Integration** for data fetching
- **Comprehensive Analysis**:
  - Personalized health insights
  - Risk assessment with scoring
  - Trend predictions
  - Health score calculation
  - Pattern detection
  - Correlation analysis
  - Time series forecasting

## Quick Start

### 1. Setup

```powershell
# Navigate to the service directory
cd bp-analysis-service

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```powershell
# Copy example env file
copy .env.example .env

# Edit .env with your Supabase credentials
notepad .env
```

Required environment variables:
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

### 3. Run the Service

```powershell
# From bp-analysis-service directory
cd app
uvicorn main:app --reload --port 8000
```

### 4. Test the API

Open: http://localhost:8000/docs

## API Endpoints

All endpoints accept POST requests with JSON body.

### Base URL: `/api/v1/analysis`

| Endpoint | Description | Request Body |
|----------|-------------|--------------|
| `/insights` | Generate health insights | `{patient_id, time_range?}` |
| `/risk-assessment` | Calculate risk score | `{patient_id, time_range?}` |
| `/predictions` | Trend predictions | `{patient_id, time_range?}` |
| `/health-score` | Overall health score | `{patient_id, time_range?}` |
| `/patterns` | Detect BP patterns | `{patient_id, time_range?}` |
| `/correlations` | Lifestyle correlations | `{patient_id, time_range?}` |
| `/forecast` | Time series forecast | `{patient_id, metric, forecast_days}` |

### Request Format

```json
{
  "patient_id": "uuid-string",
  "time_range": {
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z"
  }
}
```

### Response Formats

All responses match your frontend TypeScript interfaces exactly.

**Insights Response:**
```json
{
  "insights": [
    {
      "id": "uuid",
      "type": "warning",
      "title": "Elevated Evening Readings",
      "message": "Your BP tends to spike in the evening",
      "priority": 2,
      "timestamp": "2024-01-15T10:30:00Z",
      "recommendations": ["Reduce salt after 6 PM"]
    }
  ]
}
```

**Risk Assessment Response:**
```json
{
  "overallRisk": "moderate",
  "riskScore": 65,
  "factors": [
    {
      "name": "Blood Pressure Variability",
      "impact": "high",
      "description": "Readings show high variability"
    }
  ],
  "recommendations": ["Maintain consistent measurement times"]
}
```

## Project Structure

```
bp-analysis-service/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings management
│   ├── models/
│   │   ├── requests.py      # Request models
│   │   └── responses.py     # Response models (match frontend)
│   ├── services/
│   │   ├── insights.py      # Insights generation
│   │   ├── risk_assessment.py
│   │   ├── predictions.py
│   │   ├── health_score.py
│   │   ├── patterns.py
│   │   ├── correlations.py
│   │   └── forecast.py
│   ├── routers/
│   │   └── analysis.py      # API endpoints
│   ├── utils/
│   │   ├── database.py      # Supabase connection
│   │   └── cache.py         # Caching logic
│   └── errors/
│       └── handlers.py      # Error handling
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Frontend Integration

### Update your `api.ts`:

```typescript
const ANALYSIS_API_URL = 'http://localhost:8000';

export const api = {
  // ... existing endpoints ...
  
  smartAnalysis: {
    getInsights: async (patientId: string, timeRange?: TimeRange) => {
      const response = await fetch(`${ANALYSIS_API_URL}/api/v1/analysis/insights`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: patientId, time_range: timeRange })
      });
      return response.json();
    },
    
    getRiskAssessment: async (patientId: string) => {
      const response = await fetch(`${ANALYSIS_API_URL}/api/v1/analysis/risk-assessment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: patientId })
      });
      return response.json();
    },
    
    // ... other endpoints ...
  }
};
```

## Error Handling

Errors return in this format:

```json
{
  "error": {
    "code": "INSUFFICIENT_DATA",
    "message": "Not enough blood pressure readings (minimum 7 required)",
    "details": { "readings_count": 3, "minimum_required": 7 }
  }
}
```

Error codes:
- `INSUFFICIENT_DATA` - Not enough data for analysis
- `PATIENT_NOT_FOUND` - Patient ID not found
- `ANALYSIS_FAILED` - Analysis computation failed
- `DATABASE_ERROR` - Database connection issue

## Testing

```powershell
# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## Deployment Options

### Railway.app
1. Push to GitHub
2. Connect Railway to repo
3. Add environment variables
4. Deploy

### Render.com
1. Create Web Service
2. Build command: `pip install -r requirements.txt`
3. Start command: `cd app && uvicorn main:app --host 0.0.0.0 --port $PORT`

### Local Production
```powershell
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Cache Management

- Default TTL: 30 minutes
- Clear patient cache: `POST /api/v1/analysis/invalidate-cache/{patient_id}`
- View stats: `GET /api/v1/analysis/cache-stats`

## License

MIT
