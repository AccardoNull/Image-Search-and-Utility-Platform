from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_kmp_endpoint():
    response = client.post(
        "/kmp",
        json={
            "text": "ABABDABACDABABCABAB",
            "pattern": "ABABCABAB"
        }
    )

    assert response.status_code == 200
    assert "steps" in response.json()

def test_search_endpoint():
    response = client.get("/search?q=cat")

    assert response.status_code == 422

    data = response.json()

    assert "detail" in data
    assert any(
        error.get("loc") == ["query", "session_id"]
        for error in data["detail"]
    )