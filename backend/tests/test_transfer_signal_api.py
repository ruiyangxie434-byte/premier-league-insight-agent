from fastapi.testclient import TestClient


def test_transfer_signal_returns_explainable_external_candidates(
    api_client: TestClient,
) -> None:
    response = api_client.get(
        "/api/clubs/liverpool/transfer-signals?position=MID"
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["club"]["slug"] == "liverpool"
    assert data["season"] == "2024-25"
    assert data["position"] == "MID"
    assert data["minimum_minutes"] == 900
    assert data["is_supported"] is True
    assert data["unavailable_reason"] is None
    assert data["club_record_count"] > 0
    assert data["peer_record_count"] > data["club_record_count"]
    assert len(data["needs"]) == 3
    assert len(data["candidates"]) == 6
    assert all(
        item["club"]["slug"] != "liverpool"
        for item in data["candidates"]
    )
    assert all(item["key_lifts"] for item in data["candidates"])
    scores = [item["signal_score"] for item in data["candidates"]]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= score <= 100 for score in scores)
    assert "不是当前名单" in data["sample_notice"]
    assert "不是成交概率" in data["decision_notice"]


def test_transfer_signal_recalculates_position_pool_and_limit(
    api_client: TestClient,
) -> None:
    response = api_client.get(
        "/api/clubs/arsenal/transfer-signals"
        "?position=FWD&minimum_minutes=1800&limit=3"
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["position"] == "FWD"
    assert data["minimum_minutes"] == 1800
    assert data["limit"] == 3
    assert len(data["candidates"]) <= 3
    assert all(item["minutes"] >= 1800 for item in data["candidates"])


def test_transfer_signal_stops_unsupported_goalkeeper_ranking(
    api_client: TestClient,
) -> None:
    response = api_client.get(
        "/api/clubs/chelsea/transfer-signals?position=GK"
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["is_supported"] is False
    assert data["candidates"] == []
    assert data["needs"] == []
    assert "门将专属指标" in data["unavailable_reason"]


def test_transfer_signal_validates_scope_and_unknown_club(
    api_client: TestClient,
) -> None:
    missing = api_client.get(
        "/api/clubs/not-a-club/transfer-signals?position=DEF"
    )
    invalid_position = api_client.get(
        "/api/clubs/liverpool/transfer-signals?position=WB"
    )
    invalid_minutes = api_client.get(
        "/api/clubs/liverpool/transfer-signals?minimum_minutes=100"
    )
    invalid_limit = api_client.get(
        "/api/clubs/liverpool/transfer-signals?limit=20"
    )

    assert missing.status_code == 404
    assert invalid_position.status_code == 422
    assert invalid_minutes.status_code == 422
    assert invalid_limit.status_code == 422
