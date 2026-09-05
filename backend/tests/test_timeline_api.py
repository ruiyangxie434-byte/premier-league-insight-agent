from fastapi.testclient import TestClient


def test_timeline_rebuilds_all_rounds_and_matches_final_table(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/form/timeline")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["season"] == "2024-25"
    assert data["total_matchweeks"] == 38
    assert data["match_count"] == 380
    assert len(data["rounds"]) == 38
    assert all(len(item["rows"]) == 20 for item in data["rounds"])
    assert all(
        row["played"] == item["matchweek"]
        for item in data["rounds"]
        for row in item["rows"]
    )

    final_rows = data["rounds"][-1]["rows"]
    assert final_rows[0]["club"]["slug"] == "liverpool"
    assert final_rows[0]["points"] == 84
    assert final_rows[-1]["club"]["slug"] == "southampton"
    assert final_rows[-1]["points"] == 12


def test_timeline_returns_movement_windows_and_zone_counts(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/form/timeline")

    assert response.status_code == 200
    data = response.json()["data"]
    stories = {item["club"]["slug"]: item for item in data["club_stories"]}
    liverpool = stories["liverpool"]
    assert liverpool["final_position"] == 1
    assert liverpool["leader_rounds"] > 0
    assert liverpool["top_four_rounds"] >= liverpool["leader_rounds"]
    assert liverpool["best_five_match_window"]["points"] <= 15
    assert liverpool["worst_five_match_window"]["points"] >= 0
    assert len(data["leader_changes"]) >= 1
    assert data["leader_changes"][0]["matchweek"] == 1
    assert data["leader_changes"][0]["previous_leader"] is None
    assert "matchweek" in data["sample_notice"]
    assert "预测" in data["sample_notice"]


def test_timeline_rejects_unsupported_season(api_client: TestClient) -> None:
    response = api_client.get("/api/form/timeline?season=2023-24")

    assert response.status_code == 404
    assert response.json()["success"] is False
