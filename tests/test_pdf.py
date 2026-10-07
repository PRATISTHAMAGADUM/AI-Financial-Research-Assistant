import os
from backend.utils.pdf_generator import generate_pdf_report

def test_pdf_report_generation():
    dummy_data = {
        "query": "What was Apple's total revenue in 2024?",
        "answer": "Apple's total revenue for 2024 reached $394.33 Billion, driven by iPhone sales.",
        "grounding_score": 0.95,
        "grounding_percentage": 95.0,
        "is_grounded": True,
        "warning_message": "",
        "claims": [
            {
                "claim": "Apple 2024 revenue reached $394.33 Billion.",
                "supported": True,
                "evidence_snippet": "Apple reported total net revenue of $394,328,000,000 in FY 2024."
            }
        ],
        "sources": [
            {
                "title": "Apple Inc. (AAPL) - 2024 Annual 10-K Report",
                "source_name": "SEC EDGAR",
                "source_url": "https://www.sec.gov/edgar/aapl",
                "company": "Apple Inc.",
                "ticker": "AAPL",
                "year": 2024,
                "document_type": "10-K Report",
                "snippet": "Total net revenue for fiscal year 2024 was $394.33B."
            }
        ],
        "search_mode": "Research Mode"
    }

    pdf_path = generate_pdf_report(dummy_data)
    assert pdf_path is not None
    assert os.path.exists(pdf_path)
    assert pdf_path.endswith(".pdf")
    assert os.path.getsize(pdf_path) > 1000
