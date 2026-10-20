"""
SQLAlchemy ORM models for document metadata, status tracking, and patent feasibility analysis.
"""
from datetime import datetime, timezone
import json
from typing import List, Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime
from app.database import Base


class DocumentModel(Base):
    __tablename__ = "documents"

    document_id = Column(String(64), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    status = Column(String(32), default="processing", index=True)  # processing, ready, failed
    current_stage = Column(String(32), default="validating")  # validating, extracting, ocr, chunking, embedding, indexing, ready, failed
    progress_percent = Column(Integer, default=0)
    num_pages = Column(Integer, default=0)
    num_chunks = Column(Integer, default=0)
    used_ocr = Column(Boolean, default=False)
    warnings_json = Column(Text, default="[]")
    error_message = Column(Text, nullable=True)
    full_text = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def warnings(self) -> List[str]:
        if not self.warnings_json:
            return []
        try:
            return json.loads(self.warnings_json)
        except Exception:
            return []

    @warnings.setter
    def warnings(self, val: List[str]):
        self.warnings_json = json.dumps(val)

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "storage_path": self.storage_path,
            "status": self.status,
            "current_stage": self.current_stage,
            "progress_percent": self.progress_percent,
            "num_pages": self.num_pages,
            "num_chunks": self.num_chunks,
            "used_ocr": self.used_ocr,
            "warnings": self.warnings,
            "error_message": self.error_message,
            "full_text": self.full_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PatentAnalysisModel(Base):
    __tablename__ = "patent_analyses"

    analysis_id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    idea_description = Column(Text, nullable=False)
    problem_solved = Column(Text, nullable=False)
    technical_solution = Column(Text, nullable=False)
    differentiation_notes = Column(Text, default="")
    target_industry = Column(String(255), nullable=True)
    jurisdiction = Column(String(64), default="United States")
    paper_ids_json = Column(Text, default="[]")
    report_json = Column(Text, default="{}")
    preliminary_assessment = Column(String(64), default="Insufficient evidence to assess")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def paper_ids(self) -> List[str]:
        if not self.paper_ids_json:
            return []
        try:
            return json.loads(self.paper_ids_json)
        except Exception:
            return []

    @paper_ids.setter
    def paper_ids(self, val: List[str]):
        self.paper_ids_json = json.dumps(val)

    @property
    def report(self) -> dict:
        if not self.report_json:
            return {}
        try:
            return json.loads(self.report_json)
        except Exception:
            return {}

    @report.setter
    def report(self, val: dict):
        self.report_json = json.dumps(val)

    def to_dict(self) -> dict:
        data = self.report.copy() if self.report else {}
        data.update({
            "analysis_id": self.analysis_id,
            "title": self.title,
            "idea_description": self.idea_description,
            "problem_solved": self.problem_solved,
            "technical_solution": self.technical_solution,
            "differentiation_notes": self.differentiation_notes,
            "target_industry": self.target_industry,
            "jurisdiction": self.jurisdiction,
            "paper_ids": self.paper_ids,
            "preliminary_assessment": self.preliminary_assessment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        })
        return data

    def to_summary_dict(self) -> dict:
        return {
            "analysis_id": self.analysis_id,
            "title": self.title,
            "preliminary_assessment": self.preliminary_assessment,
            "jurisdiction": self.jurisdiction,
            "num_papers": len(self.paper_ids),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
