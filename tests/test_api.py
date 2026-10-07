from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_api_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "health_check" in data

def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "chroma_documents_count" in data
    assert data["chroma_documents_count"] >= 0

def test_api_companies():
    response = client.get("/api/companies")
    assert response.status_code == 200
    data = response.json()
    assert "companies" in data
    assert isinstance(data["companies"], list)
    assert len(data["companies"]) > 0

def test_api_history():
    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert isinstance(data["history"], list)

def test_api_query_endpoint():
    payload = {
        "query": "What was Apple's total revenue in 2024?",
        "ticker": "AAPL",
        "year": 2024,
        "search_mode": "Research Mode",
        "top_k": 2
    }
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "answer" in data
    assert "grounding_score" in data
    assert "sources" in data
