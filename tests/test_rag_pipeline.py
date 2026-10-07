from backend.rag.pipeline import rag_pipeline
from backend.grounding.verifier import grounding_verifier

def test_grounding_verifier():
    from langchain_core.documents import Document
    doc = Document(page_content="Apple revenue for 2025 was $394,328,000,000.", metadata={"ticker": "AAPL"})

    answer = "Apple's 2025 revenue reached $394,328,000,000."
    res = grounding_verifier.verify_answer(answer, [doc])
    assert res.grounding_score > 0.5
    assert res.is_grounded is True

    # Test hallucinated answer
    hallucinated = "Apple acquired Tesla for $100 Billion in 2025."
    res_hal = grounding_verifier.verify_answer(hallucinated, [doc])
    assert res_hal.grounding_score < 1.0

def test_rag_pipeline_answer_question():
    res = rag_pipeline.answer_question("What was Apple's revenue in 2025?", ticker="AAPL")
    assert "query" in res
    assert "answer" in res
    assert "grounding_score" in res
    assert "sources" in res
    assert isinstance(res["sources"], list)
    assert len(res["sources"]) > 0
    assert "title" in res["sources"][0]
    assert "source_url" in res["sources"][0]

def test_insufficient_information():
    # Query for a non-existent metric or empty context
    res = rag_pipeline.answer_question("What is the quantum teleportation expenditure for XYZ?", ticker="NONEXISTENT_XYZ_123")
    assert "answer" in res
    assert "sources" in res
