from backend.ingestion.collector import collector
from backend.rag.processor import doc_processor

def test_document_processing_chunks():
    reports = collector.collect_company_documents("AAPL", years=[2025])
    assert len(reports) > 0

    chunks = doc_processor.process_financial_report(reports[0])
    assert len(chunks) > 0

    # Check section types present
    section_types = [c.metadata.get("section_type") for c in chunks]
    assert "financial_metrics" in section_types
    assert "risk_factors" in section_types

    # Check metadata integrity
    for chunk in chunks:
        assert chunk.metadata["ticker"] == "AAPL"
        assert chunk.metadata["company"] == "Apple Inc."
        assert chunk.metadata["year"] == 2025
        assert "chunk_id" in chunk.metadata
        assert len(chunk.page_content) > 0
