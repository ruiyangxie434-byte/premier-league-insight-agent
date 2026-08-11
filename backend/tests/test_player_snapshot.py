import json
from pathlib import Path


SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "kaggle_pl_players_2024_25.json"
)


def test_player_snapshot_is_pinned_complete_and_transfer_aware() -> None:
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    summary = snapshot["summary"]
    source = snapshot["source"]
    players = snapshot["players"]

    assert snapshot["season"] == "2024-25"
    assert summary == {
        "records": 574,
        "unique_players": 562,
        "clubs": 20,
        "transfer_records": 12,
        "minimum_450_minutes": 400,
        "total_minutes": 750930,
    }
    assert source["dataset_version"] == 1
    assert source["license_name"] == "CC0: Public Domain"
    assert source["archive_sha256"] == (
        "fc5ae5fbf93195232bde675ea9fb693765e1e17c3adcccd0554916081b6b4bf5"
    )
    assert len({player["slug"] for player in players}) == 574
    assert {
        (player["club_slug"], player["minutes"])
        for player in players
        if player["full_name"] == "Marcus Rashford"
    } == {("aston-villa", 444), ("manchester-united", 978)}
