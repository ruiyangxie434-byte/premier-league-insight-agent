import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_portrait_manifest_covers_every_player_record_and_identity() -> None:
    stats = json.loads(
        (ROOT / "data/processed/kaggle_pl_players_2024_25.json").read_text(
            encoding="utf-8"
        )
    )["players"]
    manifest = json.loads(
        (ROOT / "data/processed/player_portraits_2024_25.json").read_text(
            encoding="utf-8"
        )
    )
    frontend_codes = json.loads(
        (ROOT / "frontend/lib/player-portrait-codes.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["season"] == "2024-25"
    assert manifest["record_count"] == len(stats) == len(manifest["players"])
    assert manifest["players"] == frontend_codes
    assert set(frontend_codes) == {player["slug"] for player in stats}

    codes_by_name: dict[str, set[int]] = defaultdict(set)
    for player in stats:
        codes_by_name[player["full_name"]].add(frontend_codes[player["slug"]])

    assert len(codes_by_name) == manifest["identity_count"] == 562
    assert all(len(codes) == 1 for codes in codes_by_name.values())
    assert len({next(iter(codes)) for codes in codes_by_name.values()}) == 562
    assert manifest["source_sha256"] == "75686051b265cbe7755ac71213ecaad21b26ee1cc46a8bafbba19c39ce894b05"
