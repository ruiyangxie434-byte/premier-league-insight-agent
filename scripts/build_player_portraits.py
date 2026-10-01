"""Build a reviewed identity manifest; never infer photo IDs from database row IDs.

Usage: python scripts/build_player_portraits.py /path/to/players_raw.csv
Input is pinned FPL 2024-25 metadata. No network or database writes are required.
"""

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "59c767596750f554ba464de94cf4fce8664a6cbe"
SOURCE_SHA256 = "75686051b265cbe7755ac71213ecaad21b26ee1cc46a8bafbba19c39ce894b05"
SOURCE_URL = (
    "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/"
    f"{SOURCE_COMMIT}/data/2024-25/players_raw.csv"
)
CLUBS = [
    "arsenal", "aston-villa", "bournemouth", "brentford",
    "brighton-and-hove-albion", "chelsea", "crystal-palace", "everton",
    "fulham", "ipswich-town", "leicester-city", "liverpool", "manchester-city",
    "manchester-united", "newcastle-united", "nottingham-forest", "southampton",
    "tottenham-hotspur", "west-ham-united", "wolverhampton-wanderers",
]

# Reviewed against the pinned source's full name, club and available birth year.
# All other mappings require a unique exact name or unique whole-name token match.
ALIASES = {
    "Ben White": 198869,
    "Emi Buendía": 195546,
    "Jaden Philogene Bidace": 481624,
    "Jáder Durán": 476344,
    "Edmond-Paris Maghoma": 220695,
    "Joshua Acheampong": 577016,
    "Idrissa Gana Gueye": 80801,
    "Vitaliy Mykolenko": 224967,
    "Joshua King": 577725,
    "Sammie Szmodics": 172453,
    "Abdul Fatawu Issahaku": 531442,
    "Victor Bernth Kristiansen": 481510,
    "Diogo Jota": 194634,
    "Kostas Tsimikas": 214285,
    "Nicolás González": 465694,
    "Chidozie Obi-Martin": 596047,
    "Valentino Livramento": 441191,
    "William Smallbone": 214466,
    "Lucas Paquetá": 224024,
    "Oliver Scarles": 536109,
}


def tokens(name: str) -> list[str]:
    name = name.translate(str.maketrans({"ø": "o", "æ": "ae", "ı": "i"}))
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.findall(r"[a-z0-9]+", name.casefold())


def normalized(name: str) -> str:
    return "".join(tokens(name))


def build_manifest(source: Path) -> dict:
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Source checksum differs from the reviewed FPL snapshot")
    snapshot = json.loads((ROOT / "data/processed/kaggle_pl_players_2024_25.json").read_text())
    rows = [r for r in csv.DictReader(source.open(encoding="utf-8-sig")) if r["element_type"] != "5"]
    by_code = {int(r["code"]): r for r in rows}
    grouped = defaultdict(list)
    for player in snapshot["players"]:
        grouped[player["full_name"]].append(player)
    entries, audit, missing = {}, {}, []
    used_codes = {}
    for name, records in grouped.items():
        clubs = {p["club_slug"] for p in records}
        birth_year = records[0]["birth_year"]
        method = "exact_name"
        if name in ALIASES:
            candidates = [by_code[ALIASES[name]]]
            method = "reviewed_alias"
        else:
            candidates = [r for r in rows if normalized(name) in {
                normalized(r["first_name"] + " " + r["second_name"]),
                normalized(r["web_name"]),
            }]
            if not candidates:
                method = "name_tokens"
                candidates = [r for r in rows if set(tokens(name)) <= set(tokens(r["first_name"] + " " + r["second_name"]))]
            if len(candidates) > 1:
                candidates = [r for r in candidates if r["birth_date"] not in {"", "None"} and int(r["birth_date"][:4]) == birth_year]
        if len(candidates) != 1:
            missing.append(name)
            continue
        row = candidates[0]
        source_club = CLUBS[int(row["team"]) - 1]
        # Neto played PL minutes for Bournemouth before his Arsenal loan; FPL
        # records the receiving club. Source: premierleague.com/en/news/4100166.
        neto_loan = name == "Neto" and source_club == "arsenal" and clubs == {"bournemouth"} and row["code"] == "69752"
        if source_club not in clubs and not neto_loan:
            raise ValueError(f"Club mismatch requires review: {name}: {clubs} / {source_club}")
        source_year = None if row["birth_date"] in {"", "None"} else int(row["birth_date"][:4])
        # Exact name + Ipswich agreement; source data disagree by one day/year.
        # This identity manifest deliberately does not overwrite the stats dataset.
        if birth_year and source_year and birth_year != source_year and name != "Leif Davis":
            raise ValueError(f"Birth-year mismatch requires review: {name}")
        code = int(row["code"])
        if code in used_codes:
            raise ValueError(f"Two identities share one photo code: {name} / {used_codes[code]}")
        used_codes[code] = name
        for player in records:
            entries[player["slug"]] = code
        audit[name] = {
            "code": code, "source_name": row["first_name"] + " " + row["second_name"],
            "source_club": source_club, "source_birth_date": None if not source_year else row["birth_date"],
            "match_method": method, "slugs": [p["slug"] for p in records],
        }
    if missing:
        raise ValueError("Unmatched identities: " + ", ".join(missing))
    return {
        "schema_version": 1, "season": "2024-25",
        "source_url": SOURCE_URL, "source_commit": SOURCE_COMMIT,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "image_origin": "https://resources.premierleague.com",
        "notice": "照片来自英超公开图片服务，服装可能随来源更新；不用于推断当前所属球队。图片权利归原权利人，统计数据的 CC0 许可不涵盖照片。",
        "record_count": len(entries), "identity_count": len(audit),
        "players": dict(sorted(entries.items())), "identities": dict(sorted(audit.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "data/processed/player_portraits_2024_25.json")
    args = parser.parse_args()
    manifest = build_manifest(args.source)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # A compact frontend copy avoids shipping the review metadata to every client.
    (ROOT / "frontend/lib/player-portrait-codes.json").write_text(json.dumps(manifest["players"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Mapped {manifest['record_count']} records / {manifest['identity_count']} identities")


if __name__ == "__main__":
    main()
