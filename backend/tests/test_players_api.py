from fastapi.testclient import TestClient


def test_player_lab_returns_full_snapshot_metadata_and_percentiles(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/players")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["season"] == "2024-25"
    assert data["minimum_minutes"] == 450
    assert data["pool_total"] == 400
    assert data["total"] == 400
    assert data["dataset_total"] == 574
    assert data["unique_player_total"] == 562
    assert data["transfer_record_total"] == 12
    assert data["items"][0]["slug"] == "jader-duran"
    assert data["items"][0]["per90"]["goals_per90"] == 0.99
    profile = data["items"][0]["percentiles"]
    assert profile["scope"] == "position_pool"
    assert profile["peer_count"] == 99
    assert profile["metrics"]["goals_per90"] == 100
    assert all(
        0 <= value <= 100
        for value in profile["metrics"].values()
    )
    assert "574 条" in data["sample_notice"]
    assert data["source_version"] == 1
    assert data["license_name"] == "CC0: Public Domain"
    assert "同位置" in data["percentile_notice"]


def test_player_lab_filters_position_club_query_and_minutes(
    api_client: TestClient,
) -> None:
    midfielders = api_client.get(
        "/api/players?position=MID&minimum_minutes=2700"
    )
    assert midfielders.status_code == 200
    midfielder_data = midfielders.json()["data"]
    assert midfielder_data["pool_total"] == 79
    assert midfielder_data["total"] == 19
    assert {
        item["slug"] for item in midfielder_data["items"]
    } >= {
        "bruno-guimaraes",
        "declan-rice",
        "youri-tielemans",
    }

    club = api_client.get(
        "/api/players?club_slug=arsenal&minimum_minutes=0&limit=100"
    )
    assert club.status_code == 200
    assert club.json()["data"]["total"] == 25
    assert {item["slug"] for item in club.json()["data"]["items"]} >= {
        "bukayo-saka",
        "declan-rice",
        "william-saliba",
    }

    query = api_client.get(
        "/api/players?query=egypt&minimum_minutes=0&limit=100"
    )
    assert query.status_code == 200
    assert {item["slug"] for item in query.json()["data"]["items"]} == {
        "mohamed-salah",
        "omar-marmoush",
        "sam-morsy",
    }


def test_player_lab_supports_sorting_and_pagination(
    api_client: TestClient,
) -> None:
    response = api_client.get(
        "/api/players?sort_by=tackles_per90&order=desc&limit=3&offset=0"
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 400
    assert len(data["items"]) == 3
    values = [item["per90"]["tackles_per90"] for item in data["items"]]
    assert values == sorted(values, reverse=True)


def test_player_detail_exposes_totals_and_position_fallback(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/players/virgil-van-dijk")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["full_name"] == "Virgil van Dijk"
    assert data["club"]["slug"] == "liverpool"
    assert data["totals"]["minutes"] == 3330
    assert data["birth_year"] == 1991
    assert data["source_kind"] == "kaggle-fbref"
    assert data["per90"]["interceptions_per90"] == 1.51
    assert data["percentiles"]["scope"] == "position_pool"
    assert data["percentiles"]["peer_count"] == 149


def test_player_lab_keeps_transfer_spells_separate(
    api_client: TestClient,
) -> None:
    villa = api_client.get("/api/players/marcus-rashford-aston-villa")
    united = api_client.get("/api/players/marcus-rashford-manchester-united")

    assert villa.status_code == 200
    assert united.status_code == 200
    villa_data = villa.json()["data"]
    united_data = united.json()["data"]
    assert villa_data["club"]["slug"] == "aston-villa"
    assert villa_data["totals"]["minutes"] == 444
    assert united_data["club"]["slug"] == "manchester-united"
    assert united_data["totals"]["minutes"] == 978
    assert villa_data["id"] != united_data["id"]


def test_player_api_validates_filters_and_unknown_player(
    api_client: TestClient,
) -> None:
    invalid_position = api_client.get("/api/players?position=STRIKER")
    assert invalid_position.status_code == 422
    assert invalid_position.json()["success"] is False

    invalid_minutes = api_client.get("/api/players?minimum_minutes=-1")
    assert invalid_minutes.status_code == 422

    missing = api_client.get("/api/players/not-a-player")
    assert missing.status_code == 404
    assert missing.json()["message"] == "未找到该球员或赛季数据"
