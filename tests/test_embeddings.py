from backend.embeddings.embedding_service import embedding_service

def test_embedding_service_query():
    query = "What was Apple's total revenue in 2025?"
    vector = embedding_service.embed_query(query)
    assert isinstance(vector, list)
    assert len(vector) > 0
    assert isinstance(vector[0], float)

def test_embedding_service_documents():
    docs = [
        "Apple Inc revenue for 2025 was $394.3 Billion.",
        "Microsoft Azure AI expanded subscription growth by 60%."
    ]
    vectors = embedding_service.embed_documents(docs)
    assert len(vectors) == 2
    assert len(vectors[0]) == len(vectors[1])
