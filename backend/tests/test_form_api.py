from fastapi.testclient import TestClient


def test_season_form_returns_complete_verified_snapshot(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/form?season=2024-25")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["season"] == "2024-25"
    assert data["snapshot_date"] == "2025-05-25"
    assert data["match_count"] == 380
    assert data["goal_count"] == 1115
    assert data["goals_per_match"] == 2.93
    assert data["home_wins"] == 155
    assert data["draws"] == 93
    assert data["away_wins"] == 132
    assert data["license_name"] == "CC0 1.0 Universal"
    assert len(data["source_commit"]) == 40
    assert len(data["items"]) == 20

    liverpool = data["items"][0]
    assert liverpool["position"] == 1
    assert liverpool["club"]["slug"] == "liverpool"
    assert liverpool["overall"] == {
        "played": 38,
        "won": 25,
        "drawn": 9,
        "lost": 4,
        "goals_for": 86,
        "goals_against": 41,
        "goal_difference": 45,
        "points": 84,
        "points_per_game": 2.21,
    }
    assert len(liverpool["recent_form"]) == 5
    assert len(liverpool["points_by_matchweek"]) == 38
    assert liverpool["points_by_matchweek"][-1] == 84


def test_form_records_reconcile_with_final_table(api_client: TestClient) -> None:
    form_response = api_client.get("/api/form")
    table_response = api_client.get("/api/standings?season=2024-25")

    assert form_response.status_code == 200
    assert table_response.status_code == 200
    form_items = {
        item["club"]["slug"]: item
        for item in form_response.json()["data"]["items"]
    }
    table_items = table_response.json()["data"]["items"]
    for table_item in table_items:
        form_item = form_items[table_item["club"]["slug"]]
        assert form_item["position"] == table_item["position"]
        assert form_item["overall"]["played"] == table_item["played"]
        assert form_item["overall"]["won"] == table_item["won"]
        assert form_item["overall"]["drawn"] == table_item["drawn"]
        assert form_item["overall"]["lost"] == table_item["lost"]
        assert form_item["overall"]["goals_for"] == table_item["goals_for"]
        assert form_item["overall"]["goals_against"] == table_item["goals_against"]
        assert form_item["overall"]["points"] == table_item["points"]
        assert form_item["home"]["played"] == 19
        assert form_item["away"]["played"] == 19
        assert form_item["points_by_matchweek"][-1] == table_item["points"]


def test_club_form_returns_38_results_and_recent_context(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/form/clubs/manchester-city")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["club"]["slug"] == "manchester-city"
    assert data["final_position"] == 3
    assert data["overall"]["played"] == 38
    assert data["overall"]["points"] == 71
    assert data["home"]["played"] == 19
    assert data["away"]["played"] == 19
    assert len(data["matches"]) == 38
    assert len(data["recent_form"]) == 5
    assert data["longest_unbeaten"] >= 1
    assert data["points_by_matchweek"][-1] == 71
    assert all(
        match["result"] in {"W", "D", "L"}
        and match["points"] in {0, 1, 3}
        and match["opponent"]["slug"] != "manchester-city"
        for match in data["matches"]
    )
    kickoff_values = [match["kickoff_at"] for match in data["matches"]]
    assert kickoff_values == sorted(kickoff_values)


def test_form_keeps_event_match_api_separate(api_client: TestClient) -> None:
    response = api_client.get("/api/matches")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["source_match_id"] == "3749448"


def test_form_rejects_unavailable_or_invalid_season(
    api_client: TestClient,
) -> None:
    unavailable = api_client.get("/api/form?season=2025-26")
    invalid = api_client.get("/api/form?season=2025")

    assert unavailable.status_code == 404
    assert unavailable.json()["message"] == (
        "当前仅提供 2024-25 赛季完整赛果快照"
    )
    assert invalid.status_code == 422
    assert invalid.json()["errors"][0]["field"] == "query.season"


def test_unknown_club_form_uses_unified_error(api_client: TestClient) -> None:
    response = api_client.get("/api/form/clubs/not-a-club")

    assert response.status_code == 404
    assert response.json()["message"] == "未找到该球队"
