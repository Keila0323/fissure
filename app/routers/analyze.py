from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.analyzer import analyze_flow

router = APIRouter()


class AnalyzeRequest(BaseModel):
    flow_description: str = Field(..., min_length=20, max_length=5000)


@router.get("/health")
async def health():
    return {"status": "ok", "service": "fissure"}


@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    try:
        result = analyze_flow(request.flow_description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
