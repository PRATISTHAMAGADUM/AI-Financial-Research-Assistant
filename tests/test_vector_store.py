from backend.ingestion.collector import collector
from backend.rag.processor import doc_processor
from backend.retrieval.vector_store import vector_store

def test_chroma_vector_store():
    # Collect & process documents for AAPL
    reports = collector.collect_company_documents("AAPL", years=[2025])
    chunks = doc_processor.process_financial_report(reports[0])

    # Insert into ChromaDB
    inserted_count = vector_store.add_documents(chunks)
    assert inserted_count > 0

    # Verify duplicate detection / update
    reinserted_count = vector_store.add_documents(chunks)
    assert reinserted_count == len(chunks)

    # Perform semantic search with filter
    results = vector_store.similarity_search("What was Apple's total revenue?", top_k=2, ticker="AAPL")
    assert len(results) > 0
    assert "AAPL" in results[0].metadata["ticker"]
    assert "revenue" in results[0].page_content.lower() or "apple" in results[0].page_content.lower()

    # Search with score
    results_with_score = vector_store.similarity_search_with_score("Apple net income", top_k=1, ticker="AAPL")
    assert len(results_with_score) == 1
    doc, score = results_with_score[0]
    assert 0.0 <= score <= 1.0

    stats = vector_store.get_collection_stats()
    assert stats["total_chunks"] >= len(chunks)
