from fastapi.testclient import TestClient


def test_squad_lens_returns_grounded_club_structure(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/clubs/liverpool/squad-lens")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["club"]["slug"] == "liverpool"
    assert data["season"] == "2024-25"
    assert data["minimum_minutes"] == 450
    assert data["record_total"] == 24
    assert data["qualified_total"] == 19
    assert data["excluded_total"] == 5
    assert data["total_minutes"] > 0
    assert len(data["position_groups"]) == 4
    assert sum(item["record_count"] for item in data["position_groups"]) == 19
    position_minutes = sum(
        item["minutes"] for item in data["position_groups"]
    )
    position_share = sum(
        item["minutes_share"] for item in data["position_groups"]
    )
    assert position_minutes == data["total_minutes"]
    assert 99.8 <= position_share <= 100.2
    assert len(data["leaders"]) == 5
    assert data["leaders"][0]["player"]["full_name"] == "Mohamed Salah"
    assert data["leaders"][1]["value"] == 29
    assert data["leaders"][2]["value"] == 18
    assert len(data["core_players"]) == 8
    assert data["core_players"][0]["minutes"] >= data["core_players"][1]["minutes"]
    assert "不是当前实时名单" in data["sample_notice"]
    assert "不用于预测" in data["method_notice"]


def test_squad_lens_recalculates_for_minimum_minutes(
    api_client: TestClient,
) -> None:
    response = api_client.get(
        "/api/clubs/arsenal/squad-lens?minimum_minutes=1800"
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["minimum_minutes"] == 1800
    assert data["qualified_total"] < data["record_total"]
    assert all(item["minutes"] >= 1800 for item in data["core_players"])


def test_squad_lens_validates_unknown_club_and_empty_pool(
    api_client: TestClient,
) -> None:
    missing = api_client.get("/api/clubs/not-a-club/squad-lens")
    empty = api_client.get(
        "/api/clubs/liverpool/squad-lens?minimum_minutes=4000"
    )
    invalid = api_client.get(
        "/api/clubs/liverpool/squad-lens?minimum_minutes=-1"
    )

    assert missing.status_code == 404
    assert empty.status_code == 404
    assert invalid.status_code == 422
