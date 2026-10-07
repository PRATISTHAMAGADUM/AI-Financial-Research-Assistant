import os
import time
import json
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="AI Financial Research Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern, Premium Dark & Slate Aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        color: #f8fafc;
    }
    
    /* Custom Header Banner */
    .main-header {
        background: linear-gradient(90deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
        padding: 24px 32px;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 24px;
    }
    
    .main-header h1 {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .main-header p {
        color: #c7d2fe;
        font-size: 1.05rem;
        margin-top: 6px;
        margin-bottom: 0;
    }

    /* Glassmorphism Metric Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }

    /* Grounding Badges */
    .grounding-high {
        background: linear-gradient(135deg, rgba(22, 163, 74, 0.2) 0%, rgba(22, 163, 74, 0.05) 100%);
        border: 1px solid #22c55e;
        color: #4ade80;
        padding: 16px 24px;
        border-radius: 12px;
        font-weight: 600;
    }
    
    .grounding-medium {
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.2) 0%, rgba(217, 119, 6, 0.05) 100%);
        border: 1px solid #f59e0b;
        color: #fbbf24;
        padding: 16px 24px;
        border-radius: 12px;
        font-weight: 600;
    }
    
    .grounding-low {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.2) 0%, rgba(220, 38, 38, 0.05) 100%);
        border: 1px solid #ef4444;
        color: #f87171;
        padding: 16px 24px;
        border-radius: 12px;
        font-weight: 600;
    }

    /* Source Citation Cards */
    .source-card {
        background: #1e293b;
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
        border-top: 1px solid rgba(255,255,255,0.05);
        border-right: 1px solid rgba(255,255,255,0.05);
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    
    .source-title {
        font-weight: 600;
        color: #818cf8;
        font-size: 0.95rem;
    }
    
    .source-url {
        color: #38bdf8;
        font-size: 0.82rem;
        text-decoration: none;
    }
    
    .source-snippet {
        color: #94a3b8;
        font-size: 0.88rem;
        margin-top: 6px;
        font-style: italic;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #090d16;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #4f46e5 0%, #6366f1 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #4338ca 0%, #4f46e5 100%);
        box-shadow: 0 6px 18px rgba(79, 70, 229, 0.5);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# Imports from backend
from backend.rag.pipeline import rag_pipeline
from backend.retrieval.vector_store import vector_store
from backend.llm.ollama_client import ollama_client
from backend.database.session import log_research_query, get_query_history, get_all_company_profiles, upsert_company_profile
from backend.utils.pdf_generator import generate_pdf_report
from backend.ingestion.collector import collector

# Header Banner
st.markdown("""
<div class="main-header">
    <h1>📈 AI Financial Research Assistant</h1>
    <p>Grounded Financial RAG System | Local Phi-3 LLM | ChromaDB | SEC EDGAR & Public Financial APIs</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation & Settings
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/000000/bar-chart.png", width=64)
    st.title("Navigation")
    
    nav_option = st.radio(
        "Select Module:",
        ["🎯 Research Assistant", "📊 Company Deep-Dive", "🗄️ Vector DB & Ingestion", "📜 History & PDF Export", "⚙️ System Status"],
        index=0
    )
    
    st.divider()
    st.subheader("🛠️ RAG Pipeline Settings")
    selected_mode = st.selectbox("Search Mode", ["Research Mode", "Quick Search"], help="Research Mode performs vector retrieval + LLM synthesis. Quick Search pulls instant structured metrics.")
    top_k_val = st.slider("Context Chunks (Top-K)", min_value=2, max_value=8, value=4)
    
    st.divider()
    # Live System Health Check Pills
    ollama_ok = ollama_client.check_health()
    chroma_count = vector_store.get_collection_count()
    
    st.caption("SYSTEM STATUS")
    if ollama_ok:
        st.success("🟢 Local LLM (Phi-3): Active")
    else:
        st.warning("🟠 Local LLM: Offline (Fallback Mode)")
    st.info(f"📚 Vector DB: {chroma_count} chunks")

# Initialize Session State
if "query_result" not in st.session_state:
    st.session_state["query_result"] = None

# Sample Preset Queries
preset_queries = [
    "What was Apple's total revenue, net income, and EPS in 2024?",
    "Compare NVIDIA and Microsoft 2024 operating cash flow and revenue growth.",
    "What is Tesla's gross profit margin and revenue breakdown for 2024?",
    "What are Microsoft's primary financial highlights and net income for 2024?"
]

# MODULE 1: Research Assistant
if nav_option == "🎯 Research Assistant":
    st.markdown("### 🔍 Financial Query & Grounded Analysis")
    
    # Preset pills
    st.caption("Click a preset sample question to populate:")
    cols_pills = st.columns(len(preset_queries))
    for idx, q_preset in enumerate(preset_queries):
        with cols_pills[idx]:
            if st.button(f"Prompt {idx+1}", key=f"btn_preset_{idx}"):
                st.session_state["query_input"] = q_preset

    # Input Form
    col_input, col_ticker, col_year = st.columns([3, 1, 1])
    with col_input:
        user_query = st.text_input(
            "Enter Financial Research Query:",
            value=st.session_state.get("query_input", "What was Apple's total revenue and net income in 2024?"),
            placeholder="e.g. Compare AAPL and MSFT net income in 2024...",
            key="input_query"
        )
    with col_ticker:
        company_ticker = st.selectbox(
            "Ticker Filter:",
            ["(All Companies)", "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META"],
            index=1
        )
    with col_year:
        year_filter = st.selectbox("Fiscal Year:", ["All Years", 2025, 2024, 2023], index=2)

    col_btn, col_space = st.columns([1, 4])
    with col_btn:
        run_query = st.button("🚀 Analyze & Verify", use_container_width=True)

    if run_query and user_query.strip():
        with st.spinner("Retrieving financial documents, generating answer, and auditing grounding evidence..."):
            start_t = time.time()
            
            ticker_param = company_ticker if company_ticker != "(All Companies)" else None
            year_param = year_filter if year_filter != "All Years" else None
            
            res = rag_pipeline.answer_question(
                query=user_query,
                ticker=ticker_param,
                year=year_param,
                top_k=top_k_val,
                search_mode=selected_mode
            )
            
            elapsed = time.time() - start_t
            res["execution_time"] = round(elapsed, 2)
            st.session_state["query_result"] = res
            
            # Save query log to DB
            log_research_query(
                query=res["query"],
                answer=res["answer"],
                ticker=ticker_param,
                year=year_param,
                search_mode=selected_mode,
                grounding_score=res["grounding_score"],
                is_grounded=res["is_grounded"],
                warning_message=res.get("warning_message", ""),
                claims=res.get("claims", []),
                sources=res.get("sources", [])
            )

    # Render Results
    res = st.session_state["query_result"]
    if res:
        st.divider()
        
        # Grounding Confidence Badge & Stats Row
        g_pct = res["grounding_percentage"]
        g_score = res["grounding_score"]
        is_gr = res["is_grounded"]
        exec_time = res.get("execution_time", 0.5)

        col_g1, col_g2, col_g3, col_g4 = st.columns([2, 1, 1, 1])
        
        with col_g1:
            if g_pct >= 85:
                st.markdown(f"""
                <div class="grounding-high">
                    <div style="font-size: 0.85rem; opacity: 0.9;">GROUNDING CONFIDENCE</div>
                    <div style="font-size: 1.8rem; font-weight: 700;">{g_pct}% ✅ HIGHLY GROUNDED</div>
                    <div style="font-size: 0.8rem; margin-top: 4px;">Verified against {len(res['sources'])} retrieved primary sources</div>
                </div>
                """, unsafe_allow_html=True)
            elif g_pct >= 70:
                st.markdown(f"""
                <div class="grounding-medium">
                    <div style="font-size: 0.85rem; opacity: 0.9;">GROUNDING CONFIDENCE</div>
                    <div style="font-size: 1.8rem; font-weight: 700;">{g_pct}% ⚠️ MODERATE GROUNDING</div>
                    <div style="font-size: 0.8rem; margin-top: 4px;">Some claims may lack direct numeric alignment</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="grounding-low">
                    <div style="font-size: 0.85rem; opacity: 0.9;">GROUNDING CONFIDENCE</div>
                    <div style="font-size: 1.8rem; font-weight: 700;">{g_pct}% ❌ LOW GROUNDING</div>
                    <div style="font-size: 0.8rem; margin-top: 4px;">Potential hallucinated figures detected</div>
                </div>
                """, unsafe_allow_html=True)

        with col_g2:
            st.metric("Retrieved Chunks", f"{res.get('retrieved_chunks_count', 0)} Chunks")
        with col_g3:
            st.metric("Claims Audited", f"{len(res.get('claims', []))} Claims")
        with col_g4:
            st.metric("Execution Speed", f"{exec_time}s")

        if res.get("warning_message"):
            st.warning(res["warning_message"])

        st.markdown("#### 📝 Executive Financial Analysis")
        st.markdown(res["answer"])

        # PDF Export Button
        st.write("")
        pdf_path = generate_pdf_report(res)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="📄 Download PDF Research Report",
                data=pdf_file,
                file_name=f"Financial_Research_{res.get('ticker', 'Report')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=False
            )

        # Tabbed Details: Claims Verification vs Primary Sources
        tab_claims, tab_sources = st.tabs(["🔬 Claim Grounding Audit", "📚 Primary Sources & SEC Citations"])
        
        with tab_claims:
            claims_list = res.get("claims", [])
            if not claims_list:
                st.info("No explicit atomic numeric claims detected to audit.")
            else:
                for idx, c in enumerate(claims_list, 1):
                    supported = c.get("supported", False)
                    claim_txt = c.get("claim", "")
                    snippet = c.get("evidence_snippet", "")

                    if supported:
                        st.markdown(f"**Claim {idx}:** ✅ `{claim_txt}`")
                        st.caption(f"📍 **Evidence Snippet:** {snippet}")
                    else:
                        st.markdown(f"**Claim {idx}:** ❌ `<span style='color:#f87171'>{claim_txt}</span>`", unsafe_allow_html=True)
                        st.caption("⚠️ **Warning:** No matching figure or key token found in retrieved financial context.")
                    st.divider()

        with tab_sources:
            sources_list = res.get("sources", [])
            if not sources_list:
                st.info("No sources retrieved.")
            else:
                for idx, src in enumerate(sources_list, 1):
                    st.markdown(f"""
                    <div class="source-card">
                        <div class="source-title">[{idx}] {src['title']} ({src['company']})</div>
                        <div style="font-size:0.8rem; color:#94a3b8;">Source: {src['source_name']} | Type: {src['document_type']}</div>
                        <a class="source-url" href="{src['source_url']}" target="_blank">🔗 View Document Source ({src['source_url']})</a>
                        <div class="source-snippet">"{src['snippet']}"</div>
                    </div>
                    """, unsafe_allow_html=True)

# MODULE 2: Company Deep-Dive & Financial Analytics
elif nav_option == "📊 Company Deep-Dive":
    st.markdown("### 📊 Multi-Company Financial Analytics & Comparison")
    
    # Financial data comparison across pre-ingested companies
    companies_data = [
        {"Ticker": "AAPL", "Company": "Apple Inc.", "Revenue ($B)": 394.33, "Net Income ($B)": 93.74, "Operating Cash Flow ($B)": 108.65, "EPS ($)": 6.11, "Profit Margin (%)": 23.77},
        {"Ticker": "MSFT", "Company": "Microsoft Corp", "Revenue ($B)": 245.12, "Net Income ($B)": 88.14, "Operating Cash Flow ($B)": 118.54, "EPS ($)": 11.80, "Profit Margin (%)": 35.96},
        {"Ticker": "NVDA", "Company": "NVIDIA Corp", "Revenue ($B)": 96.31, "Net Income ($B)": 53.00, "Operating Cash Flow ($B)": 40.50, "EPS ($)": 2.15, "Profit Margin (%)": 55.03},
        {"Ticker": "GOOGL", "Company": "Alphabet Inc.", "Revenue ($B)": 307.39, "Net Income ($B)": 73.80, "Operating Cash Flow ($B)": 101.74, "EPS ($)": 5.80, "Profit Margin (%)": 24.01},
        {"Ticker": "AMZN", "Company": "Amazon.com Inc.", "Revenue ($B)": 574.78, "Net Income ($B)": 30.43, "Operating Cash Flow ($B)": 84.94, "EPS ($)": 2.90, "Profit Margin (%)": 5.29},
        {"Ticker": "TSLA", "Company": "Tesla Inc.", "Revenue ($B)": 96.77, "Net Income ($B)": 14.99, "Operating Cash Flow ($B)": 13.25, "EPS ($)": 3.12, "Profit Margin (%)": 15.49},
        {"Ticker": "META", "Company": "Meta Platforms", "Revenue ($B)": 134.90, "Net Income ($B)": 39.10, "Operating Cash Flow ($B)": 71.10, "EPS ($)": 14.87, "Profit Margin (%)": 28.98}
    ]
    
    df_fin = pd.DataFrame(companies_data)

    st.markdown("#### 📈 Key Financial Metrics Comparison (2024 Fiscal Year)")
    st.dataframe(df_fin, use_container_width=True, hide_index=True)

    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        fig_rev = px.bar(
            df_fin,
            x="Ticker",
            y="Revenue ($B)",
            color="Company",
            title="Total Revenue Comparison ($ Billions)",
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_rev.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_rev, use_container_width=True)

    with col_chart2:
        fig_net = px.bar(
            df_fin,
            x="Ticker",
            y="Net Income ($B)",
            color="Company",
            title="Net Income Comparison ($ Billions)",
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Emerald
        )
        fig_net.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_net, use_container_width=True)

    fig_margin = px.line(
        df_fin,
        x="Company",
        y="Profit Margin (%)",
        markers=True,
        title="Net Profit Margin (%) Across Tech & Automotive Giants",
        template="plotly_dark"
    )
    fig_margin.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_margin, use_container_width=True)

# MODULE 3: Vector DB & Ingestion
elif nav_option == "🗄️ Vector DB & Ingestion":
    st.markdown("### 🗄️ ChromaDB Vector Database & Data Collector")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.metric("Total Ingested Document Chunks", f"{vector_store.get_collection_count()} Chunks")
    with col_v2:
        st.metric("Embedding Model", settings.EMBEDDING_MODEL_NAME)

    st.divider()
    st.markdown("#### 📥 Ingest Custom Stock Ticker Data")
    
    col_in1, col_in2 = st.columns([2, 1])
    with col_in1:
        custom_ticker = st.text_input("Enter Ticker Symbol (e.g. AMD, NFLX, JPM):", value="AMD").upper()
    with col_in2:
        ingest_btn = st.button("📥 Collect & Index Data", use_container_width=True)

    if ingest_btn and custom_ticker:
        with st.spinner(f"Collecting financial reports and building vector embeddings for {custom_ticker}..."):
            count = rag_pipeline.ensure_ticker_ingested(custom_ticker, years=[2023, 2024, 2025])
            upsert_company_profile(custom_ticker, f"{custom_ticker} Corporation", "Technology", "Hardware", vector_store.get_collection_count())
            st.success(f"✅ Ingested {count} chunks for {custom_ticker}! Total collection count: {vector_store.get_collection_count()}")

    st.divider()
    st.markdown("#### 🔍 ChromaDB Vector Search Inspection")
    search_q = st.text_input("Test Direct Vector Similarity Search:", value="Operating Cash Flow and margins")
    if st.button("Run Vector Search"):
        results = vector_store.similarity_search(search_q, top_k=3)
        for i, doc in enumerate(results, 1):
            st.markdown(f"**Chunk #{i}** | Ticker: `{doc.metadata.get('ticker')}` | Year: `{doc.metadata.get('year')}` | Score Distance: `{doc.metadata.get('distance', 'N/A')}`")
            st.code(doc.page_content[:300] + "...")

# MODULE 4: History & Saved Reports
elif nav_option == "📜 History & PDF Export":
    st.markdown("### 📜 Research Query History & Exported Reports")
    
    history_logs = get_query_history(limit=50)
    if not history_logs:
        st.info("No research query logs found in SQLite database yet. Perform a query in the Research Assistant tab!")
    else:
        st.caption(f"Displaying last {len(history_logs)} research queries:")
        for log in history_logs:
            g_score = log.get("grounding_percentage", 100.0)
            st.markdown(f"""
            <div class="source-card">
                <div style="display: flex; justify-content: space-between;">
                    <span class="source-title">Q: {log['query']}</span>
                    <span style="color:{'#4ade80' if g_score>=85 else '#fbbf24' if g_score>=70 else '#f87171'}; font-weight:bold;">
                        Grounding: {g_score}%
                    </span>
                </div>
                <div style="font-size:0.8rem; color:#94a3b8; margin-top:4px;">
                    Ticker: <b>{log.get('ticker') or 'All'}</b> | Mode: {log.get('search_mode')} | Timestamp: {log.get('created_at')}
                </div>
                <div style="margin-top:8px; color:#cbd5e1; font-size:0.9rem;">
                    {log['answer'][:250]}...
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # PDF export for historic log item
            if st.button(f"Export PDF for Query #{log['id']}", key=f"hist_pdf_{log['id']}"):
                p_path = generate_pdf_report(log)
                with open(p_path, "rb") as f:
                    st.download_button(
                        label=f"📥 Download PDF Log #{log['id']}",
                        data=f,
                        file_name=f"Report_Query_{log['id']}.pdf",
                        mime="application/pdf"
                    )

# MODULE 5: System Status
elif nav_option == "⚙️ System Status":
    st.markdown("### ⚙️ System Architecture & Connection Status")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    
    with col_s1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("#### 🤖 Local LLM (Ollama)")
        st.write(f"**Model:** `{settings.OLLAMA_MODEL}`")
        st.write(f"**URL:** `{settings.OLLAMA_BASE_URL}`")
        st.write(f"**Status:** {'🟢 Online' if ollama_ok else '🟠 Offline (Fallback active)'}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_s2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("#### 📚 Vector Database")
        st.write(f"**Engine:** `ChromaDB Persistent`")
        st.write(f"**Collection:** `{settings.CHROMA_COLLECTION_NAME}`")
        st.write(f"**Chunks:** `{vector_store.get_collection_count()}`")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_s3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("#### 🗄️ Database & APIs")
        st.write(f"**DB:** `SQLite ({settings.SQLITE_DB_PATH})`")
        st.write(f"**Alpha Vantage Key:** `{'Configured' if settings.ALPHA_VANTAGE_API_KEY else 'Demo'}`")
        st.write(f"**Grounding Threshold:** `{int(settings.GROUNDING_THRESHOLD * 100)}%`")
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 🏗️ Architecture Overview")
    st.code("""
    [ User / Web UI ]
            │
            ▼
    [ Financial RAG Pipeline ]
       ├── 1. Ingestion Engine (SEC EDGAR & Financial APIs)
       ├── 2. Vector Retriever (ChromaDB + SentenceTransformers)
       ├── 3. LLM Synthesis (Local Phi-3 via Ollama)
       ├── 4. Grounding Verifier (Numeric & Token Overlap Guardrails)
       └── 5. Output Formatter (Grounding Score Badge + PDF Generator + SQLite Log)
    """, language="text")
