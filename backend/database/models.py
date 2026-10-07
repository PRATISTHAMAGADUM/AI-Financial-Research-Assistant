import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ResearchQueryLog(Base):
    __tablename__ = "research_query_logs"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    ticker = Column(String(20), nullable=True, index=True)
    year = Column(Integer, nullable=True)
    search_mode = Column(String(50), default="Research Mode")
    answer = Column(Text, nullable=False)
    grounding_score = Column(Float, default=1.0)
    grounding_percentage = Column(Float, default=100.0)
    is_grounded = Column(Boolean, default=True)
    warning_message = Column(Text, nullable=True)
    claims_json = Column(Text, nullable=True)
    sources_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "query": self.query,
            "ticker": self.ticker,
            "year": self.year,
            "search_mode": self.search_mode,
            "answer": self.answer,
            "grounding_score": self.grounding_score,
            "grounding_percentage": self.grounding_percentage,
            "is_grounded": self.is_grounded,
            "warning_message": self.warning_message,
            "claims": json.loads(self.claims_json) if self.claims_json else [],
            "sources": json.loads(self.sources_json) if self.sources_json else [],
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    documents_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "ticker": self.ticker,
            "company_name": self.company_name,
            "sector": self.sector,
            "industry": self.industry,
            "documents_count": self.documents_count,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }
