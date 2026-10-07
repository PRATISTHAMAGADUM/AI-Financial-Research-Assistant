import os
import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.config import settings
from backend.rag.pipeline import rag_pipeline
from backend.retrieval.vector_store import vector_store
from backend.llm.ollama_client import ollama_client
from backend.database.session import (
    log_research_query,
    get_query_history,
    get_all_company_profiles,
    upsert_company_profile
)
from backend.utils.pdf_generator import generate_pdf_report
from backend.ingestion.collector import collector

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade AI Financial Research Assistant API powered by Local LLM (Phi-3) & ChromaDB RAG",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class QueryRequest(BaseModel):
    query: str = Field(..., description="Financial query or question", json_schema_extra={"example": "What was Apple's total revenue and net income in 2024?"})
    ticker: Optional[str] = Field(None, description="Stock ticker symbol (e.g. AAPL, MSFT)", json_schema_extra={"example": "AAPL"})
    year: Optional[int] = Field(None, description="Financial fiscal year", json_schema_extra={"example": 2024})
    quarter: Optional[str] = Field(None, description="Fiscal quarter (Q1, Q2, Q3, Q4, Annual)")
    search_mode: str = Field("Research Mode", description="Search mode: 'Research Mode' or 'Quick Search'")
    top_k: int = Field(4, ge=1, le=10, description="Number of context chunks to retrieve")

class ClaimVerification(BaseModel):
    claim: str
    supported: bool
    evidence_snippet: str

class SourceCitation(BaseModel):
    title: str
    source_name: str
    source_url: str
    company: str
    ticker: str
    year: Optional[int] = None
    quarter: Optional[str] = None
    document_type: str
    snippet: str

class QueryResponse(BaseModel):
    query: str
    search_mode: str
    answer: str
    grounding_score: float
    grounding_percentage: float
    is_grounded: bool
    warning_message: str
    claims: List[ClaimVerification]
    sources: List[SourceCitation]
    retrieved_chunks_count: int

class IngestRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol", json_schema_extra={"example": "NVDA"})
    company_name: Optional[str] = Field(None, description="Company full name", json_schema_extra={"example": "NVIDIA Corporation"})
    years: Optional[List[int]] = Field([2023, 2024, 2025], description="Fiscal years to ingest")

class IngestResponse(BaseModel):
    ticker: str
    message: str
    documents_ingested: int

class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    ollama_status: str
    ollama_model: str
    chroma_documents_count: int
    database_status: str

# API Endpoints
@app.get("/", tags=["General"])
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs_url": "/docs",
        "health_check": "/api/health"
    }

@app.get("/api/health", response_model=HealthResponse, tags=["General"])
def health_check():
    """System health check endpoint verifying local LLM, vector store, and database status."""
    ollama_ok = ollama_client.check_health()
    chroma_count = vector_store.get_collection_count()
    
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENV,
        "ollama_status": "connected" if ollama_ok else "disconnected / fallback mode",
        "ollama_model": settings.OLLAMA_MODEL,
        "chroma_documents_count": chroma_count,
        "database_status": "connected"
    }

@app.post("/api/query", response_model=QueryResponse, tags=["RAG Research"])
def execute_query(req: QueryRequest, background_tasks: BackgroundTasks):
    """
    Execute AI Financial Research Query:
    - Auto-ingests ticker if missing
    - Retrieves top-k grounded chunks from ChromaDB
    - Generates grounded answer via Phi-3 / Local LLM
    - Verifies numeric & claim-level grounding score
    - Returns citations & logs query to DB
    """
    try:
        res = rag_pipeline.answer_question(
            query=req.query,
            ticker=req.ticker,
            year=req.year,
            quarter=req.quarter,
            top_k=req.top_k,
            search_mode=req.search_mode
        )

        # Background task to log query to SQLite database
        background_tasks.add_task(
            log_research_query,
            query=res["query"],
            answer=res["answer"],
            ticker=req.ticker,
            year=req.year,
            search_mode=res.get("search_mode", "Research Mode"),
            grounding_score=res["grounding_score"],
            is_grounded=res["is_grounded"],
            warning_message=res.get("warning_message", ""),
            claims=res.get("claims", []),
            sources=res.get("sources", [])
        )

        return res
    except Exception as e:
        logger.error(f"Error executing research query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest", response_model=IngestResponse, tags=["Ingestion"])
def ingest_company_data(req: IngestRequest):
    """Ingest financial reports for a company ticker into ChromaDB."""
    try:
        ticker = req.ticker.upper().strip()
        count = rag_pipeline.ensure_ticker_ingested(ticker, years=req.years)

        # Update profile
        overview = collector.get_company_overview(ticker)
        company_name = req.company_name or overview.get("Name") or f"{ticker} Inc."
        sector = overview.get("Sector", "Technology")
        industry = overview.get("Industry", "Software / Tech")

        upsert_company_profile(
            ticker=ticker,
            name=company_name,
            sector=sector,
            industry=industry,
            docs_count=vector_store.get_collection_count()
        )

        return {
            "ticker": ticker,
            "message": f"Successfully ingested financial data for {ticker}",
            "documents_ingested": count
        }
    except Exception as e:
        logger.error(f"Error ingesting company data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/companies", tags=["Companies"])
def list_companies():
    """List all available company profiles and vector store counts."""
    profiles = get_all_company_profiles()
    if not profiles:
        # Default seed profiles if database is fresh
        default_tickers = [
            ("AAPL", "Apple Inc.", "Technology", "Consumer Electronics"),
            ("MSFT", "Microsoft Corporation", "Technology", "Software Infrastructure"),
            ("NVDA", "NVIDIA Corporation", "Technology", "Semiconductors"),
            ("GOOGL", "Alphabet Inc.", "Technology", "Internet Content & Information"),
            ("AMZN", "Amazon.com Inc.", "Consumer Cyclical", "Internet Retail"),
            ("TSLA", "Tesla Inc.", "Consumer Cyclical", "Auto Manufacturers"),
            ("META", "Meta Platforms Inc.", "Technology", "Internet Content & Information")
        ]
        for t, n, s, i in default_tickers:
            upsert_company_profile(t, n, s, i, vector_store.get_collection_count())
        profiles = get_all_company_profiles()
    return {"companies": profiles, "total_chroma_chunks": vector_store.get_collection_count()}

@app.get("/api/history", tags=["Research History"])
def fetch_history(limit: int = Query(30, ge=1, le=100)):
    """Fetch past research query logs."""
    history = get_query_history(limit=limit)
    return {"history": history, "count": len(history)}

@app.post("/api/export-pdf", tags=["Reports"])
def export_pdf_report(payload: Dict[str, Any]):
    """Generate and download styled PDF research report."""
    try:
        pdf_path = generate_pdf_report(payload)
        filename = os.path.basename(pdf_path)
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
