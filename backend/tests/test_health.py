from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_unified_response() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Premier League Insight Agent API is running",
        "data": {
            "service": "Premier League Insight Agent API",
            "status": "healthy",
            "environment": "development",
            "version": "0.12.0",
        },
    }


def test_unknown_route_returns_unified_error() -> None:
    response = client.get("/api/not-found")

    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["data"] is None
