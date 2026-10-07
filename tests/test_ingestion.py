import pytest
from backend.ingestion.collector import collector, FinancialDataCollector
from backend.ingestion.models import FinancialReportDocument

def test_ticker_validation():
    col = FinancialDataCollector()
    assert col.validate_ticker("aapl") == "AAPL"
    assert col.validate_ticker(" msft ") == "MSFT"
    with pytest.raises(ValueError):
        col.validate_ticker("")

def test_collect_company_documents_aapl():
    docs = collector.collect_company_documents("AAPL", years=[2024, 2025])
    assert len(docs) > 0
    doc = docs[0]
    assert isinstance(doc, FinancialReportDocument)
    assert doc.ticker == "AAPL"
    assert doc.company_name == "Apple Inc."
    assert doc.year in [2024, 2025]
    assert doc.metrics.revenue is not None
    metadata = doc.to_metadata()
    assert metadata["ticker"] == "AAPL"
    assert "year" in metadata
    assert "source_name" in metadata

def test_collect_company_overview():
    overview = collector.get_company_overview("MSFT")
    assert overview is not None
    assert "Name" in overview or "Symbol" in overview
