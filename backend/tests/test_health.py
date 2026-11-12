"""Tests for GET /health."""


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_body(client):
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert data["service"] == "agentlens"
