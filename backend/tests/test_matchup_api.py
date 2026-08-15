def test_matchup_returns_two_club_profiles_and_direct_meetings(api_client):
    response = api_client.get("/api/form/matchup?club_a=liverpool&club_b=arsenal")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["season"] == "2024-25"
    assert data["club_a"]["club"]["slug"] == "liverpool"
    assert data["club_b"]["club"]["slug"] == "arsenal"
    assert data["club_a"]["overall"]["played"] == 38
    assert data["club_b"]["overall"]["played"] == 38
    assert len(data["head_to_head"]["meetings"]) == 2
    assert data["head_to_head"]["club_a_goals"] + data["head_to_head"]["club_b_goals"] > 0
    assert len(data["dimensions"]) == 8
    assert {item["advantage"] for item in data["dimensions"]} <= {"club_a", "club_b", "even"}
    assert any("不是下一场比赛的胜率预测" in item for item in data["summary"])


def test_matchup_rejects_same_club(api_client):
    response = api_client.get("/api/form/matchup?club_a=arsenal&club_b=arsenal")
    assert response.status_code == 422
    assert response.json()["message"] == "请选择两支不同球队"


def test_matchup_rejects_unknown_club(api_client):
    response = api_client.get("/api/form/matchup?club_a=arsenal&club_b=not-a-club")
    assert response.status_code == 404


def test_matchup_rejects_unsupported_season(api_client):
    response = api_client.get("/api/form/matchup?club_a=arsenal&club_b=liverpool&season=2023-24")
    assert response.status_code == 404
