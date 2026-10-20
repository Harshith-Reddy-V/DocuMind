"""
Patent Feasibility Analyzer API Routes.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Depends

from app.models.schemas import (
    PatentAnalysisRequest,
    PatentFeasibilityReport,
    PatentAnalysisSummaryItem,
)
from app.services import patent_service
from app.utils.rate_limiter import check_rate_limit

router = APIRouter(prefix="/api/patent", tags=["patent"])


@router.post("/analyze", response_model=PatentFeasibilityReport, dependencies=[Depends(check_rate_limit)])
async def analyze_patent_idea(request: PatentAnalysisRequest):
    """
    Execute an evidence-based patent feasibility evaluation of a proposed invention idea
    against one or more selected research papers.
    """
    if not request.title or not request.title.strip():
        raise HTTPException(status_code=400, detail="Project title cannot be empty.")
    if not request.problem_solved or not request.problem_solved.strip():
        raise HTTPException(status_code=400, detail="Problem solved cannot be empty.")
    if not request.technical_solution or not request.technical_solution.strip():
        raise HTTPException(status_code=400, detail="Technical solution cannot be empty.")
    if not request.idea_description or not request.idea_description.strip():
        raise HTTPException(status_code=400, detail="Idea description cannot be empty.")

    try:
        report = patent_service.run_patent_feasibility_analysis(request)
        return report
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail="Patent feasibility analysis timed out.")
    except RuntimeError as e:
        if "429" in str(e) or "exhausted" in str(e).lower():
            raise HTTPException(status_code=429, detail="Gemini rate limit or quota exceeded. Please try again shortly.")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform patent analysis: {str(e)}")


@router.get("/analyses", response_model=List[PatentAnalysisSummaryItem])
async def list_saved_analyses():
    """List all previously saved patent feasibility evaluations."""
    try:
        return patent_service.list_patent_analyses()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list patent analyses: {str(e)}")


@router.get("/analyses/{analysis_id}", response_model=PatentFeasibilityReport)
async def get_saved_analysis(analysis_id: str):
    """Retrieve full details of a saved patent feasibility report."""
    report = patent_service.get_patent_analysis(analysis_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Patent analysis '{analysis_id}' not found.")
    return report


@router.delete("/analyses/{analysis_id}")
async def delete_saved_analysis(analysis_id: str):
    """Delete a saved patent feasibility report."""
    deleted = patent_service.delete_patent_analysis(analysis_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Patent analysis '{analysis_id}' not found.")
    return {"status": "deleted", "analysis_id": analysis_id}
