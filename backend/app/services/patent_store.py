"""
Persistent storage for Patent Feasibility Analyses backed by SQLite and SQLAlchemy.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from app.database import SessionLocal, init_db
from app.models.database_models import PatentAnalysisModel

init_db()


def save_patent_analysis(
    analysis_id: Any = None,
    title: Optional[str] = None,
    idea_description: Optional[str] = None,
    problem_solved: Optional[str] = None,
    technical_solution: Optional[str] = None,
    differentiation_notes: Optional[str] = None,
    target_industry: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    paper_ids: Optional[List[str]] = None,
    report: Optional[Dict[str, Any]] = None,
    preliminary_assessment: Optional[str] = None,
    **kwargs
) -> dict:
    """Save or update a patent feasibility analysis record in SQLite."""
    if isinstance(analysis_id, dict):
        d = analysis_id
        analysis_id = d.get("analysis_id")
        title = d.get("title")
        idea_description = d.get("idea_description", "")
        problem_solved = d.get("problem_solved", "")
        technical_solution = d.get("technical_solution", "")
        differentiation_notes = d.get("differentiation_notes", "")
        target_industry = d.get("target_industry")
        jurisdiction = d.get("jurisdiction", "United States")
        paper_ids = d.get("paper_ids", [])
        preliminary_assessment = d.get("preliminary_assessment", "Insufficient evidence to assess")
        report = d
    with SessionLocal() as db:
        existing = db.query(PatentAnalysisModel).filter(PatentAnalysisModel.analysis_id == analysis_id).first()
        if existing:
            existing.title = title
            existing.idea_description = idea_description
            existing.problem_solved = problem_solved
            existing.technical_solution = technical_solution
            existing.differentiation_notes = differentiation_notes or ""
            existing.target_industry = target_industry
            existing.jurisdiction = jurisdiction or "United States"
            existing.paper_ids = paper_ids
            existing.report = report
            existing.preliminary_assessment = preliminary_assessment
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing.to_dict()
        else:
            model = PatentAnalysisModel(
                analysis_id=analysis_id,
                title=title,
                idea_description=idea_description,
                problem_solved=problem_solved,
                technical_solution=technical_solution,
                differentiation_notes=differentiation_notes or "",
                target_industry=target_industry,
                jurisdiction=jurisdiction or "United States",
                preliminary_assessment=preliminary_assessment,
            )
            model.paper_ids = paper_ids
            model.report = report
            db.add(model)
            db.commit()
            db.refresh(model)
            return model.to_dict()


def get_patent_analysis(analysis_id: str) -> Optional[dict]:
    """Retrieve full patent analysis by ID."""
    with SessionLocal() as db:
        record = db.query(PatentAnalysisModel).filter(PatentAnalysisModel.analysis_id == analysis_id).first()
        return record.to_dict() if record else None


def list_patent_analyses() -> List[dict]:
    """List summary items for all patent analyses ordered by creation time descending."""
    with SessionLocal() as db:
        records = db.query(PatentAnalysisModel).order_by(PatentAnalysisModel.created_at.desc()).all()
        return [r.to_summary_dict() for r in records]


def delete_patent_analysis(analysis_id: str) -> bool:
    """Delete a patent analysis by ID."""
    with SessionLocal() as db:
        record = db.query(PatentAnalysisModel).filter(PatentAnalysisModel.analysis_id == analysis_id).first()
        if record:
            db.delete(record)
            db.commit()
            return True
        return False
