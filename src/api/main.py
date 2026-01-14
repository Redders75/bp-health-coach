"""
FastAPI application for the BP Health Coach API.
"""
from datetime import date
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.features.query_answering import QueryEngine
from src.features.daily_briefing import DailyBriefingGenerator
from src.features.scenario_testing import ScenarioEngine
from src.data.database import init_database


# Initialize FastAPI app
app = FastAPI(
    title="BP Health Coach API",
    description="AI-powered blood pressure health coaching API",
    version="0.1.0"
)

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_database()


# Request/Response models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    confidence: float
    model_used: Optional[str] = None
    tokens: int = 0


class ScenarioRequest(BaseModel):
    changes: dict
    current_bp: Optional[float] = None


class ScenarioResponse(BaseModel):
    current_bp: float
    predicted_bp: float
    bp_change: float
    confidence_low: float
    confidence_high: float
    timeline_weeks: int
    feasibility: str
    recommendations: list


class BriefingResponse(BaseModel):
    date: str
    content: str


# API endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "BP Health Coach"}


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Answer a natural language health query.

    Args:
        request: Query request with question and optional session ID

    Returns:
        Natural language response with metadata
    """
    try:
        engine = QueryEngine(request.session_id)
        result = engine.ask_with_metadata(request.query)

        return QueryResponse(
            response=result['response'],
            session_id=result['session_id'],
            intent=result['intent'],
            confidence=result['confidence'],
            model_used=result.get('model_used'),
            tokens=result.get('tokens', 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/briefing", response_model=BriefingResponse)
async def get_briefing(target_date: Optional[str] = None):
    """
    Get the daily health briefing.

    Args:
        target_date: Optional date string (YYYY-MM-DD), defaults to today

    Returns:
        Daily briefing content
    """
    try:
        generator = DailyBriefingGenerator()

        if target_date:
            parsed_date = date.fromisoformat(target_date)
        else:
            parsed_date = date.today()

        content = generator.generate_briefing(parsed_date)

        return BriefingResponse(
            date=parsed_date.isoformat(),
            content=content
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scenario", response_model=ScenarioResponse)
async def test_scenario(request: ScenarioRequest):
    """
    Test a what-if scenario.

    Args:
        request: Scenario with proposed changes

    Returns:
        Scenario analysis results
    """
    try:
        engine = ScenarioEngine()
        result = engine.test_scenario(request.changes, request.current_bp)

        return ScenarioResponse(
            current_bp=result.current_bp,
            predicted_bp=result.predicted_bp,
            bp_change=result.bp_change,
            confidence_low=result.confidence_interval[0],
            confidence_high=result.confidence_interval[1],
            timeline_weeks=result.timeline_weeks,
            feasibility=result.feasibility,
            recommendations=result.recommendations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run with: uvicorn src.api.main:app --reload
