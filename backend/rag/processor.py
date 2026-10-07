import logging
import uuid
from typing import List, Dict, Any
from langchain_core.documents import Document
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        class RecursiveCharacterTextSplitter:
            def __init__(self, chunk_size=600, chunk_overlap=100, separators=None):
                self.chunk_size = chunk_size
                self.chunk_overlap = chunk_overlap
            def split_text(self, text: str) -> List[str]:
                chunks = []
                start = 0
                while start < len(text):
                    end = min(start + self.chunk_size, len(text))
                    chunks.append(text[start:end])
                    start += self.chunk_size - self.chunk_overlap
                return chunks
from backend.ingestion.models import FinancialReportDocument

logger = logging.getLogger(__name__)

class FinancialDocumentProcessor:
    """Processes collected financial reports into semantically structured documents and chunks for RAG."""

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "; ", " ", ""]
        )

    def process_financial_report(self, report: FinancialReportDocument) -> List[Document]:
        """
        Convert a single FinancialReportDocument into a list of enriched LangChain Document chunks.
        Includes dedicated section chunks (Metrics, Risks, Events, Narrative) to optimize retrieval.
        """
        chunks: List[Document] = []
        base_meta = report.to_metadata()

        # 1. Dedicated Structured Metrics Chunk
        if report.metrics:
            m = report.metrics
            metrics_text = (
                f"Company: {report.company_name} ({report.ticker})\n"
                f"Year: {report.year} | Quarter: {report.quarter} | Document: {report.document_type}\n"
                f"Financial Performance Summary:\n"
                f"- Revenue: ${m.revenue:,.2f} USD\n" if m.revenue is not None else ""
            )
            if m.net_income is not None:
                metrics_text += f"- Net Income: ${m.net_income:,.2f} USD\n"
            if m.eps is not None:
                metrics_text += f"- Earnings Per Share (EPS): ${m.eps:.2f} USD\n"
            if m.operating_income is not None:
                metrics_text += f"- Operating Income: ${m.operating_income:,.2f} USD\n"
            if m.total_assets is not None:
                metrics_text += f"- Total Assets: ${m.total_assets:,.2f} USD\n"
            if m.total_liabilities is not None:
                metrics_text += f"- Total Liabilities: ${m.total_liabilities:,.2f} USD\n"
            if m.operating_cash_flow is not None:
                metrics_text += f"- Operating Cash Flow: ${m.operating_cash_flow:,.2f} USD\n"
            if m.revenue_growth is not None:
                metrics_text += f"- Revenue Growth: {m.revenue_growth:.2f}%\n"
            if m.profit_growth is not None:
                metrics_text += f"- Net Income Growth: {m.profit_growth:.2f}%\n"
            if m.profit_margin is not None:
                metrics_text += f"- Profit Margin: {m.profit_margin:.2f}%\n"
            metrics_text += f"Source: {report.source_name} ({report.source_url})"

            metrics_meta = dict(base_meta)
            metrics_meta["chunk_id"] = str(uuid.uuid4())
            metrics_meta["section_type"] = "financial_metrics"
            chunks.append(Document(page_content=metrics_text, metadata=metrics_meta))

        # 2. Risk Factors Section Chunk
        if report.risk_factors:
            risks_text = (
                f"Company: {report.company_name} ({report.ticker})\n"
                f"Year: {report.year} Risk Factors & Business Uncertainties:\n" +
                "\n".join([f"- {rf}" for rf in report.risk_factors]) +
                f"\nSource: {report.source_name}"
            )
            risk_meta = dict(base_meta)
            risk_meta["chunk_id"] = str(uuid.uuid4())
            risk_meta["section_type"] = "risk_factors"
            chunks.append(Document(page_content=risks_text, metadata=risk_meta))

        # 3. Financial Events Chunk
        if report.financial_events:
            events_text = (
                f"Company: {report.company_name} ({report.ticker})\n"
                f"Year: {report.year} Corporate Financial Events:\n" +
                "\n".join([f"- {ev}" for ev in report.financial_events]) +
                f"\nSource: {report.source_name}"
            )
            events_meta = dict(base_meta)
            events_meta["chunk_id"] = str(uuid.uuid4())
            events_meta["section_type"] = "financial_events"
            chunks.append(Document(page_content=events_text, metadata=events_meta))

        # 4. Chunk full narrative text using Recursive Character Splitter
        if report.text_content:
            text_splits = self.text_splitter.split_text(report.text_content)
            for i, split in enumerate(text_splits):
                chunk_meta = dict(base_meta)
                chunk_meta["chunk_id"] = str(uuid.uuid4())
                chunk_meta["section_type"] = "narrative_text"
                chunk_meta["chunk_index"] = i
                # Prepend header to give standalone context to the chunk
                header = f"[{report.company_name} ({report.ticker}) - {report.year} {report.document_type}]\n"
                chunks.append(Document(page_content=header + split, metadata=chunk_meta))

        logger.info(f"Generated {len(chunks)} chunks for {report.ticker} {report.year}")
        return chunks

    def process_reports_batch(self, reports: List[FinancialReportDocument]) -> List[Document]:
        """Process a list of FinancialReportDocument instances into Document chunks."""
        all_chunks: List[Document] = []
        for r in reports:
            all_chunks.extend(self.process_financial_report(r))
        return all_chunks

doc_processor = FinancialDocumentProcessor()
