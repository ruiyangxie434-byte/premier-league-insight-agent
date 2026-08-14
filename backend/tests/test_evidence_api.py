def test_evidence_catalog_exposes_coverage_and_boundaries(api_client):
    response = api_client.get("/api/evidence")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["source_count"] == 4
    assert data["total_records"] == 1002
    assert data["season_focus"] == "2024-25"
    assert {source["id"] for source in data["sources"]} == {
        "premier-league-table",
        "openfootball-results",
        "kaggle-fbref-players",
        "statsbomb-open-data",
    }
    player_source = next(source for source in data["sources"] if source["id"] == "kaggle-fbref-players")
    assert player_source["status"] == "limited"
    assert any("转会" in item for item in player_source["limitations"])

