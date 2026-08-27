from fastapi.testclient import TestClient


def test_club_briefing_combines_season_squad_and_recruitment(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/clubs/liverpool/briefing")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["club"]["slug"] == "liverpool"
    assert data["season"] == "2024-25"
    assert data["minimum_minutes"] == 900
    assert data["season_summary"]["final_position"] == 1
    assert data["season_summary"]["overall"]["played"] == 38
    assert data["season_summary"]["overall"]["points"] == 84
    assert len(data["season_summary"]["recent_form"]) == 5
    assert data["squad"]["club"]["slug"] == "liverpool"
    assert data["squad"]["minimum_minutes"] == 900
    assert len(data["squad"]["position_groups"]) == 4
    assert [item["position"] for item in data["recruitment"]] == [
        "DEF",
        "MID",
        "FWD",
    ]
    assert all(len(item["needs"]) == 3 for item in data["recruitment"])
    assert all(item["top_candidate"] is not None for item in data["recruitment"])
    assert len(data["headlines"]) == 6
    assert len(data["sources"]) == 2
    assert any("不是签约建议" in item for item in data["limitations"])


def test_club_briefing_recalculates_shared_minute_contract(
    api_client: TestClient,
) -> None:
    response = api_client.get(
        "/api/clubs/arsenal/briefing?minimum_minutes=1800"
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["minimum_minutes"] == 1800
    assert data["squad"]["minimum_minutes"] == 1800
    assert data["squad"]["qualified_total"] < data["squad"]["record_total"]
    assert all(
        item["top_candidate"] is None
        or item["top_candidate"]["minutes"] >= 1800
        for item in data["recruitment"]
    )


def test_club_briefing_validates_snapshot_scope(
    api_client: TestClient,
) -> None:
    missing = api_client.get("/api/clubs/not-a-club/briefing")
    unsupported_season = api_client.get(
        "/api/clubs/liverpool/briefing?season=2025-26"
    )
    invalid_minutes = api_client.get(
        "/api/clubs/liverpool/briefing?minimum_minutes=200"
    )
    unsupported_minutes = api_client.get(
        "/api/clubs/liverpool/briefing?minimum_minutes=901"
    )

    assert missing.status_code == 404
    assert unsupported_season.status_code == 404
    assert invalid_minutes.status_code == 422
    assert unsupported_minutes.status_code == 422
