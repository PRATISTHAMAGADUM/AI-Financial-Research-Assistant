# 📈 AI Financial Research Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31%2B-FF4B4B.svg)](https://streamlit.io/)
[![ChromaDB](https://img.shields.io/badge/Vector%20DB-ChromaDB-purple.svg)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An **Enterprise-Grade AI Financial Research Assistant** built with **Retrieval-Augmented Generation (RAG)**, **Local Phi-3 LLM**, **ChromaDB Vector Store**, and a **Strict Numeric Grounding Verification Engine** to prevent AI hallucinations in financial reporting.

---

## 🌟 Key Features

- **🎯 Grounded AI Financial Research**: Query financial filings, SEC 10-K statements, revenue figures, net income, cash flows, and operating metrics with verified precision.
- **🔬 Claim-Level Grounding Verification**: Audits every numeric claim and figure in generated responses against primary SEC source documents to guarantee 100% data integrity.
- **📄 Automated PDF Report Generator**: Generates exportable **Executive Financial Research Reports** in PDF format complete with **Grounding Confidence Badges (%)**, claim breakdowns, and SEC citations.
- **📊 Visual Multi-Company Analytics**: Interactive Plotly dashboard comparing Revenue, Net Income, Operating Cash Flow, EPS, and Profit Margins across tech & automotive giants (`AAPL`, `MSFT`, `NVDA`, `GOOGL`, `AMZN`, `TSLA`, `META`).
- **📥 Custom Stock Ticker Ingestion**: Ingest and index financial data for any custom company ticker symbol (e.g. `AMD`, `NFLX`, `JPM`, `DIS`) into ChromaDB on demand.
- **🚀 Dual Mode Execution**: Interactive Streamlit Web Application + FastAPI REST API server with OpenAPI (Swagger) documentation.
- **🗄️ SQLite History & Bookmarks**: Automatically logs research queries, grounding confidence percentages, timestamps, and exported report links.

---

## 🏗️ System Architecture

```
[ User / Streamlit Web UI ] ◄──► [ FastAPI REST API Server ]
                                          │
                                          ▼
                         [ Financial RAG Orchestrator ]
       ┌──────────────────────────────────┼──────────────────────────────────┐
       ▼                                  ▼                                  ▼
[ SEC & API Ingestion ]         [ ChromaDB Vector Store ]          [ Local Phi-3 LLM ]
 (Collector & Chunker)         (SentenceTransformers Embeddings)      (Ollama & Fallback)
       │                                  │                                  │
       └──────────────────────────────────┴──────────────────────────────────┘
                                          │
                                          ▼
                          [ Grounding Verifier Engine ]
                          (Numeric Overlap & Guardrails)
                                          │
                        ┌─────────────────┴─────────────────┐
                        ▼                                   ▼
          [ Executive PDF Generator ]            [ SQLite Query Logs ]
```

---

## 📁 Repository Structure

```text
AI Financial Research Assistant/
├── app.py                      # Interactive Streamlit Web Dashboard
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── backend/
│   ├── api/                    # FastAPI REST endpoints & routes
│   │   ├── main.py             # REST API server
│   │   └── __init__.py
│   ├── config.py               # Pydantic Settings configuration
│   ├── database/               # SQLite ORM models & session manager
│   │   ├── models.py
│   │   └── session.py
│   ├── embeddings/             # SentenceTransformers embedding service
│   │   └── embedding_service.py
│   ├── grounding/              # Numeric claim verification engine
│   │   └── verifier.py
│   ├── ingestion/              # SEC EDGAR & financial API collectors
│   │   ├── collector.py
│   │   ├── public_sources.py
│   │   ├── alpha_vantage.py
│   │   └── models.py
│   ├── llm/                    # Local Phi-3 / Ollama client & fallback
│   │   └── ollama_client.py
│   ├── rag/                    # Financial RAG execution pipeline
│   │   ├── pipeline.py
│   │   └── processor.py
│   ├── retrieval/              # ChromaDB persistent vector store manager
│   │   └── vector_store.py
│   └── utils/                  # PDF report generator utility
│       └── pdf_generator.py
├── scripts/
│   └── seed_data.py            # Data pre-population CLI script
└── tests/                      # Pytest test suite
    ├── test_api.py
    ├── test_database.py
    ├── test_pdf.py
    └── test_rag_pipeline.py
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** installed
- (Optional) [Ollama](https://ollama.com) installed with `phi3` model (`ollama run phi3`)

### 2. Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/PRATISTHAMAGADUM/AI-Financial-Research-Assistant.git
   cd AI-Financial-Research-Assistant
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Environment & Seed Data**:
   ```bash
   cp .env.example .env
   python -m scripts.seed_data
   ```

---

## 🏃 Running the Application

### Option A: Run Streamlit Web Application (Recommended)
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### Option B: Run FastAPI REST API Server
```bash
uvicorn backend.api.main:app --reload --port 8000
```
Access interactive API docs at `http://localhost:8000/docs`.

### Option C: Run Test Suite
```bash
pytest
```

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more details.
