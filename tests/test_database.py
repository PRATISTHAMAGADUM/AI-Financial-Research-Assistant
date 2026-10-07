from backend.database.session import (
    log_research_query,
    get_query_history,
    upsert_company_profile,
    get_all_company_profiles
)

def test_database_logging_and_profiles():
    # Test logging a query
    log_entry = log_research_query(
        query="What was Apple's 2024 revenue?",
        answer="Apple's revenue in 2024 was $394.33 Billion.",
        ticker="AAPL",
        year=2024,
        search_mode="Research Mode",
        grounding_score=0.95,
        is_grounded=True,
        claims=[{"claim": "Apple 2024 revenue $394.33B", "supported": True}],
        sources=[{"title": "AAPL SEC 10-K", "source_url": "https://www.sec.gov"}]
    )
    
    assert log_entry is not None
    assert log_entry.ticker == "AAPL"
    assert log_entry.grounding_score == 0.95

    # Test history fetching
    history = get_query_history(limit=10)
    assert len(history) > 0
    assert any(h["query"] == "What was Apple's 2024 revenue?" for h in history)

    # Test company profiles
    upsert_company_profile("AAPL", "Apple Inc.", "Technology", "Consumer Electronics", docs_count=16)
    profiles = get_all_company_profiles()
    assert len(profiles) > 0
    assert any(p["ticker"] == "AAPL" for p in profiles)
