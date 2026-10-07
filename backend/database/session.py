import json
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.config import settings
from backend.database.models import Base, ResearchQueryLog, CompanyProfile

logger = logging.getLogger(__name__)

# Create SQLite engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

def get_db():
    """Dependency for FastAPI DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def log_research_query(
    query: str,
    answer: str,
    ticker: str = None,
    year: int = None,
    search_mode: str = "Research Mode",
    grounding_score: float = 1.0,
    is_grounded: bool = True,
    warning_message: str = "",
    claims: list = None,
    sources: list = None
) -> ResearchQueryLog:
    """Save query result to database log."""
    db: Session = SessionLocal()
    try:
        log_entry = ResearchQueryLog(
            query=query,
            ticker=ticker.upper() if ticker else None,
            year=year,
            search_mode=search_mode,
            answer=answer,
            grounding_score=grounding_score,
            grounding_percentage=round(grounding_score * 100, 1),
            is_grounded=is_grounded,
            warning_message=warning_message,
            claims_json=json.dumps(claims or []),
            sources_json=json.dumps(sources or [])
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception as e:
        db.rollback()
        logger.error(f"Error logging research query: {e}")
        return None
    finally:
        db.close()

def get_query_history(limit: int = 50) -> list:
    """Fetch recent research queries from database."""
    db: Session = SessionLocal()
    try:
        logs = db.query(ResearchQueryLog).order_by(ResearchQueryLog.created_at.desc()).limit(limit).all()
        return [log.to_dict() for log in logs]
    except Exception as e:
        logger.error(f"Error fetching query history: {e}")
        return []
    finally:
        db.close()

def upsert_company_profile(ticker: str, name: str, sector: str = "Technology", industry: str = "Financial Tech", docs_count: int = 0):
    """Insert or update company metadata profile."""
    db: Session = SessionLocal()
    try:
        clean_ticker = ticker.upper().strip()
        profile = db.query(CompanyProfile).filter(CompanyProfile.ticker == clean_ticker).first()
        if not profile:
            profile = CompanyProfile(
                ticker=clean_ticker,
                company_name=name,
                sector=sector,
                industry=industry,
                documents_count=docs_count
            )
            db.add(profile)
        else:
            profile.company_name = name
            if docs_count > 0:
                profile.documents_count = docs_count
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating company profile: {e}")
    finally:
        db.close()

def get_all_company_profiles() -> list:
    """Fetch all stored company profiles."""
    db: Session = SessionLocal()
    try:
        profiles = db.query(CompanyProfile).all()
        return [p.to_dict() for p in profiles]
    except Exception as e:
        logger.error(f"Error fetching company profiles: {e}")
        return []
    finally:
        db.close()

# Initialize DB on module import
init_db()
