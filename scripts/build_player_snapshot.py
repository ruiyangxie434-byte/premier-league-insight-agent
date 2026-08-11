#!/usr/bin/env python3
"""Build the reproducible 2024-25 Premier League player snapshot.

The application never downloads player data at runtime.  This script reads the
pinned Kaggle v1 archive, selects the Premier League 2024-25 rows, normalizes
the small set of fields used by the product, validates league-wide invariants,
and writes the compact JSON committed under ``data/processed``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.request import urlopen

DATASET_OWNER = "emrey3lmaz"
DATASET_SLUG = "top-5-league-football-player-stats-2017-2025"
DATASET_VERSION = 1
DATASET_URL = f"https://www.kaggle.com/datasets/{DATASET_OWNER}/{DATASET_SLUG}"
DOWNLOAD_URL = (
    f"https://www.kaggle.com/api/v1/datasets/download/"
    f"{DATASET_OWNER}/{DATASET_SLUG}"
)
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
SOURCE_FILE = "Top5_League_Players_2017to2024_dataset.csv"
EXPECTED_ARCHIVE_SHA256 = (
    "fc5ae5fbf93195232bde675ea9fb693765e1e17c3adcccd0554916081b6b4bf5"
)
EXPECTED_CSV_SHA256 = (
    "298ee166002a5fc8759000d8c739cd046c85adbea51f2a17716cbdb19725db45"
)
SOURCE_LEAGUE = "ENG-Premier League"
SOURCE_SEASON = "2425"
SEASON = "2024-25"

TEAM_SLUGS = {
    "Arsenal": "arsenal",
    "Aston Villa": "aston-villa",
    "Bournemouth": "bournemouth",
    "Brentford": "brentford",
    "Brighton": "brighton-and-hove-albion",
    "Chelsea": "chelsea",
    "Crystal Palace": "crystal-palace",
    "Everton": "everton",
    "Fulham": "fulham",
    "Ipswich Town": "ipswich-town",
    "Leicester City": "leicester-city",
    "Liverpool": "liverpool",
    "Manchester City": "manchester-city",
    "Manchester Utd": "manchester-united",
    "Newcastle Utd": "newcastle-united",
    "Nott'ham Forest": "nottingham-forest",
    "Southampton": "southampton",
    "Tottenham": "tottenham-hotspur",
    "West Ham": "west-ham-united",
    "Wolves": "wolverhampton-wanderers",
}

NATIONALITIES = {
    "": "Unknown",
    "ALB": "Albania",
    "ALG": "Algeria",
    "ARG": "Argentina",
    "AUS": "Australia",
    "AUT": "Austria",
    "BAN": "Bangladesh",
    "BEL": "Belgium",
    "BFA": "Burkina Faso",
    "BRA": "Brazil",
    "CAN": "Canada",
    "CHI": "Chile",
    "CIV": "Cote d'Ivoire",
    "CMR": "Cameroon",
    "COD": "DR Congo",
    "COL": "Colombia",
    "CRO": "Croatia",
    "CZE": "Czechia",
    "DEN": "Denmark",
    "ECU": "Ecuador",
    "EGY": "Egypt",
    "ENG": "England",
    "ESP": "Spain",
    "FRA": "France",
    "GAB": "Gabon",
    "GAM": "Gambia",
    "GER": "Germany",
    "GHA": "Ghana",
    "GNB": "Guinea-Bissau",
    "GRE": "Greece",
    "HAI": "Haiti",
    "HUN": "Hungary",
    "IRL": "Republic of Ireland",
    "IRQ": "Iraq",
    "ISL": "Iceland",
    "ITA": "Italy",
    "JAM": "Jamaica",
    "JPN": "Japan",
    "KOR": "South Korea",
    "KVX": "Kosovo",
    "MAR": "Morocco",
    "MEX": "Mexico",
    "MLI": "Mali",
    "MSR": "Montserrat",
    "NED": "Netherlands",
    "NGA": "Nigeria",
    "NIR": "Northern Ireland",
    "NOR": "Norway",
    "NZL": "New Zealand",
    "PAR": "Paraguay",
    "POL": "Poland",
    "POR": "Portugal",
    "ROU": "Romania",
    "SCO": "Scotland",
    "SEN": "Senegal",
    "SRB": "Serbia",
    "SUI": "Switzerland",
    "SVK": "Slovakia",
    "SWE": "Sweden",
    "TUR": "Turkey",
    "UKR": "Ukraine",
    "URU": "Uruguay",
    "USA": "United States",
    "UZB": "Uzbekistan",
    "WAL": "Wales",
    "ZAM": "Zambia",
    "ZIM": "Zimbabwe",
}

POSITION_MAP = {
    "FW": "FWD",
    "MF": "MID",
    "DF": "DEF",
    "GK": "GK",
}


def read_archive(source: str) -> bytes:
    if source.startswith(("https://", "http://")):
        with urlopen(source, timeout=90) as response:  # noqa: S310
            return response.read()
    return Path(source).read_bytes()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def slugify(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .casefold()
    )
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")


def integer(row: dict[str, str], key: str) -> int:
    value = row.get(key, "").strip()
    return int(value) if value else 0


def decimal(row: dict[str, str], key: str) -> float:
    value = row.get(key, "").strip().replace(",", ".")
    return round(float(value), 3) if value else 0.0


def load_source_rows(archive: bytes) -> tuple[bytes, list[dict[str, str]]]:
    archive_digest = sha256(archive)
    if archive_digest != EXPECTED_ARCHIVE_SHA256:
        raise ValueError(
            "Kaggle archive checksum changed: "
            f"expected {EXPECTED_ARCHIVE_SHA256}, found {archive_digest}"
        )

    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        names = bundle.namelist()
        if names != [SOURCE_FILE]:
            raise ValueError(f"Unexpected archive files: {names}")
        source_csv = bundle.read(SOURCE_FILE)

    csv_digest = sha256(source_csv)
    if csv_digest != EXPECTED_CSV_SHA256:
        raise ValueError(
            "Kaggle CSV checksum changed: "
            f"expected {EXPECTED_CSV_SHA256}, found {csv_digest}"
        )

    reader = csv.DictReader(
        source_csv.decode("utf-8-sig").splitlines(),
        delimiter=";",
    )
    rows = [
        row
        for row in reader
        if row["league"] == SOURCE_LEAGUE and row["season"] == SOURCE_SEASON
    ]
    return source_csv, rows


def build_snapshot(archive: bytes) -> dict[str, Any]:
    source_csv, rows = load_source_rows(archive)
    name_counts = Counter(row["player"] for row in rows)
    records: list[dict[str, Any]] = []

    for row in rows:
        team = row["team"]
        if team not in TEAM_SLUGS:
            raise ValueError(f"Unknown Premier League team: {team}")
        nationality_code = row["nation_"]
        if nationality_code not in NATIONALITIES:
            raise ValueError(f"Unknown nationality code: {nationality_code}")

        base_slug = slugify(row["player"])
        club_slug = TEAM_SLUGS[team]
        slug = (
            f"{base_slug}-{club_slug}"
            if name_counts[row["player"]] > 1
            else base_slug
        )
        source_position = row["pos_"].split(",", maxsplit=1)[0]
        try:
            position = POSITION_MAP[source_position]
        except KeyError as exc:
            raise ValueError(f"Unknown position: {row['pos_']}") from exc

        born = row["born_"].strip()
        records.append(
            {
                "full_name": row["player"],
                "slug": slug,
                "club_slug": club_slug,
                "position": position,
                "nationality": NATIONALITIES[nationality_code],
                "nationality_code": nationality_code or None,
                "birth_year": int(born) if born else None,
                "appearances": integer(row, "Playing Time_MP"),
                "starts": integer(row, "Playing Time_Starts"),
                "minutes": integer(row, "Playing Time_Min"),
                "goals": integer(row, "Performance_Gls"),
                "assists": integer(row, "Performance_Ast"),
                "shots": integer(row, "Standard_Sh"),
                "key_passes": integer(row, "KP_"),
                "tackles": integer(row, "Tackles_Tkl"),
                "interceptions": integer(row, "Int_"),
                "expected_goals": decimal(row, "Expected_xG"),
            }
        )

    records.sort(
        key=lambda item: (
            item["club_slug"],
            item["full_name"].casefold(),
            item["slug"],
        )
    )
    validate_records(records)

    return {
        "schema_version": 1,
        "source": {
            "name": "Top 5 League Football Player Stats (2017-2025)",
            "dataset_url": DATASET_URL,
            "download_url": DOWNLOAD_URL,
            "dataset_version": DATASET_VERSION,
            "source_file": SOURCE_FILE,
            "source_updated_at": "2026-04-18T14:17:36.57Z",
            "license_name": "CC0: Public Domain",
            "license_url": LICENSE_URL,
            "archive_sha256": sha256(archive),
            "csv_sha256": sha256(source_csv),
            "upstream_note": "Collected from FBref with the soccerdata library.",
        },
        "competition": "English Premier League",
        "season": SEASON,
        "source_season": SOURCE_SEASON,
        "summary": {
            "records": len(records),
            "unique_players": len({item["full_name"] for item in records}),
            "clubs": len({item["club_slug"] for item in records}),
            "transfer_records": len(records)
            - len({item["full_name"] for item in records}),
            "minimum_450_minutes": sum(
                item["minutes"] >= 450 for item in records
            ),
            "total_minutes": sum(item["minutes"] for item in records),
        },
        "players": records,
    }


def validate_records(records: list[dict[str, Any]]) -> None:
    if len(records) != 574:
        raise ValueError(f"Expected 574 player-team records, found {len(records)}")
    if len({item["full_name"] for item in records}) != 562:
        raise ValueError("Expected 562 unique player names")
    if {item["club_slug"] for item in records} != set(TEAM_SLUGS.values()):
        raise ValueError("Snapshot club set does not match the 20-club mapping")
    if len({item["slug"] for item in records}) != len(records):
        raise ValueError("Player record slugs must be unique")
    if sum(item["minutes"] >= 450 for item in records) != 400:
        raise ValueError("Expected 400 records with at least 450 minutes")
    if sum(item["minutes"] for item in records) != 750_930:
        raise ValueError("Unexpected total playing minutes")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=DOWNLOAD_URL,
        help="Pinned Kaggle v1 ZIP path or download URL",
    )
    parser.add_argument(
        "--output",
        default="data/processed/kaggle_pl_players_2024_25.json",
        help="Output JSON path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot = build_snapshot(read_archive(args.input))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = snapshot["summary"]
    print(
        f"Wrote {summary['records']} player-team records "
        f"({summary['unique_players']} names, {summary['clubs']} clubs) "
        f"for {SEASON} to {output}"
    )


if __name__ == "__main__":
    main()
