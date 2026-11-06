import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_db_health_endpoint():
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_chat_session_creation():
    response = client.post("/api/v1/chat/new-session")
    assert response.status_code == 200
    assert "session_id" in response.json()


def test_chat_flow():
    session_res = client.post("/api/v1/chat/new-session")
    session_id = session_res.json()["session_id"]

    chat_res = client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": "My bathroom ceiling is leaking"}
    )
    assert chat_res.status_code == 200
    assert "message" in chat_res.json()
