from fastapi.testclient import TestClient

from app.core.config import Settings
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
            "version": "0.15.0",
        },
    }


def test_unknown_route_returns_unified_error() -> None:
    response = client.get("/api/not-found")

    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["data"] is None


def test_default_cors_origins_cover_both_local_frontend_aliases() -> None:
    settings = Settings(_env_file=None)

    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_development_cors_upgrades_legacy_single_origin_env() -> None:
    settings = Settings(
        _env_file=None,
        app_env="development",
        frontend_origins="http://localhost:3000",
    )

    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
