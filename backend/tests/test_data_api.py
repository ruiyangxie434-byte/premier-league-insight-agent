from fastapi.testclient import TestClient


def test_club_list_returns_complete_2024_25_league(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/clubs")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total"] == 20
    assert body["data"]["player_total"] == 574
    assert body["data"]["season"] == "2024-25"
    assert body["data"]["is_complete"] is True
    assert len(body["data"]["items"]) == 20
    assert all(
        club["source_kind"] == "reference"
        for club in body["data"]["items"]
    )
    assert {
        club["slug"]
        for club in body["data"]["items"]
    } == {
        "arsenal",
        "aston-villa",
        "bournemouth",
        "brentford",
        "brighton-and-hove-albion",
        "chelsea",
        "crystal-palace",
        "everton",
        "fulham",
        "ipswich-town",
        "leicester-city",
        "liverpool",
        "manchester-city",
        "manchester-united",
        "newcastle-united",
        "nottingham-forest",
        "southampton",
        "tottenham-hotspur",
        "west-ham-united",
        "wolverhampton-wanderers",
    }


def test_club_detail_includes_full_player_snapshot(api_client: TestClient) -> None:
    response = api_client.get("/api/clubs/liverpool")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Liverpool"
    assert data["stadium"]["name"] == "Anfield"
    assert len(data["players"]) == 24
    assert {player["full_name"] for player in data["players"]} >= {
        "Mohamed Salah",
        "Virgil van Dijk",
    }
    assert all(player["source_kind"] == "kaggle-fbref" for player in data["players"])
    assert len(data["featured_matches"]) == 1
    assert data["featured_matches"][0]["source_match_id"] == "3749448"


def test_club_list_exposes_valid_stadium_coordinates_for_map(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/clubs")

    assert response.status_code == 200
    clubs = response.json()["data"]["items"]
    assert len(clubs) == 20
    assert all(club["stadium"]["name"] for club in clubs)
    assert all(
        49 <= club["stadium"]["latitude"] <= 56
        and -6 <= club["stadium"]["longitude"] <= 2
        for club in clubs
    )
    assert len(
        {
            (
                club["stadium"]["latitude"],
                club["stadium"]["longitude"],
            )
            for club in clubs
        }
    ) == 20


def test_unknown_club_uses_unified_error(api_client: TestClient) -> None:
    response = api_client.get("/api/clubs/not-a-club")

    assert response.status_code == 404
    assert response.json() == {
        "success": False,
        "message": "未找到该球队",
        "data": None,
        "errors": None,
    }


def test_standings_return_complete_verified_snapshot(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/standings?season=2024-25")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["season"] == "2024-25"
    assert data["total"] == 20
    assert data["is_partial"] is False
    assert data["snapshot_date"] == "2025-05-25"
    assert data["source_name"] == "Premier League official table"
    assert [item["position"] for item in data["items"]] == list(range(1, 21))
    assert data["items"][0]["club"]["slug"] == "liverpool"
    assert data["items"][0]["points"] == 84
    assert data["items"][11]["club"]["slug"] == "crystal-palace"
    assert data["items"][11]["drawn"] == 14
    assert data["items"][-1]["club"]["slug"] == "southampton"
    assert data["items"][-1]["points"] == 12
    assert sum(item["goals_for"] for item in data["items"]) == 1115
    assert sum(item["goals_against"] for item in data["items"]) == 1115


def test_standings_validate_season_format(api_client: TestClient) -> None:
    response = api_client.get("/api/standings?season=2025")

    assert response.status_code == 422
    assert response.json()["success"] is False
    assert response.json()["errors"][0]["field"] == "query.season"


def test_standings_reject_unavailable_season(api_client: TestClient) -> None:
    response = api_client.get("/api/standings?season=2025-26")

    assert response.status_code == 404
    assert response.json()["message"] == "当前仅提供 2024-25 赛季最终积分榜"
