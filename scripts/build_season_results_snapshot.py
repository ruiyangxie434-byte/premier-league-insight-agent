#!/usr/bin/env python3
"""Build a compact Premier League result snapshot from OpenFootball.

The application reads the generated JSON at runtime and never downloads
season data while serving requests.  The source URL is pinned to a Git commit
so the 2024-25 snapshot can be reproduced without silently changing results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
from zoneinfo import ZoneInfo

SOURCE_COMMIT = "4f413c4b20129e51d43439a0f4d2c4d1b1be7482"
SOURCE_REPOSITORY = "https://github.com/openfootball/eng-england"
SOURCE_PATH = "2024-25/1-premierleague.txt"
SOURCE_URL = f"{SOURCE_REPOSITORY}/blob/{SOURCE_COMMIT}/{SOURCE_PATH}"
RAW_URL = (
    "https://raw.githubusercontent.com/openfootball/eng-england/"
    f"{SOURCE_COMMIT}/{SOURCE_PATH}"
)
LICENSE_URL = f"{SOURCE_REPOSITORY}/blob/{SOURCE_COMMIT}/LICENSE.md"
SEASON = "2024-25"
COMPETITION = "English Premier League"

TEAM_SLUGS = {
    "AFC Bournemouth": "bournemouth",
    "Arsenal FC": "arsenal",
    "Aston Villa FC": "aston-villa",
    "Brentford FC": "brentford",
    "Brighton & Hove Albion FC": "brighton-and-hove-albion",
    "Chelsea FC": "chelsea",
    "Crystal Palace FC": "crystal-palace",
    "Everton FC": "everton",
    "Fulham FC": "fulham",
    "Ipswich Town FC": "ipswich-town",
    "Leicester City FC": "leicester-city",
    "Liverpool FC": "liverpool",
    "Manchester City FC": "manchester-city",
    "Manchester United FC": "manchester-united",
    "Newcastle United FC": "newcastle-united",
    "Nottingham Forest FC": "nottingham-forest",
    "Southampton FC": "southampton",
    "Tottenham Hotspur FC": "tottenham-hotspur",
    "West Ham United FC": "west-ham-united",
    "Wolverhampton Wanderers FC": "wolverhampton-wanderers",
}

MATCHDAY_RE = re.compile(r"^\s*[▪•]\s*Matchday\s+(?P<number>\d+)\s*$")
DATE_RE = re.compile(
    r"^\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+"
    r"(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})"
    r"(?:\s+(?P<year>\d{4}))?\s*$"
)
MATCH_RE = re.compile(
    r"^\s*(?:(?P<time>\d{1,2}:\d{2})\s+)?"
    r"(?P<home>.+?)\s+v\s+(?P<away>.+?)\s+"
    r"(?P<home_score>\d+)-(?P<away_score>\d+)"
    r"(?:\s+\(\d+-\d+\))?\s*$"
)


def read_text(source: str) -> str:
    if source.startswith(("https://", "http://")):
        with urlopen(source, timeout=30) as response:  # noqa: S310
            return response.read().decode("utf-8-sig")
    return Path(source).read_text(encoding="utf-8-sig")


def source_match_id(
    matchweek: int,
    home_slug: str,
    away_slug: str,
) -> str:
    identity = f"{SEASON}|{matchweek}|{home_slug}|{away_slug}"
    digest = hashlib.sha1(identity.encode(), usedforsecurity=False).hexdigest()
    return f"of-2425-{digest[:12]}"


def parse_results(source_text: str) -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    current_matchweek: int | None = None
    current_date: datetime | None = None
    current_year = 2024
    current_time: str | None = None
    london = ZoneInfo("Europe/London")

    for line_number, line in enumerate(source_text.splitlines(), start=1):
        matchday = MATCHDAY_RE.match(line)
        if matchday:
            current_matchweek = int(matchday.group("number"))
            continue

        date_match = DATE_RE.match(line)
        if date_match:
            if date_match.group("year"):
                current_year = int(date_match.group("year"))
            date_text = (
                f"{current_year} {date_match.group('month')} "
                f"{date_match.group('day')}"
            )
            current_date = datetime.strptime(date_text, "%Y %b %d")
            current_time = None
            continue

        result = MATCH_RE.match(line)
        if not result:
            continue
        if current_matchweek is None or current_date is None:
            raise ValueError(
                f"Result before matchday/date context on line {line_number}"
            )

        if result.group("time"):
            current_time = result.group("time")
        if current_time is None:
            raise ValueError(f"Missing kickoff time on line {line_number}")

        home_name = result.group("home").strip()
        away_name = result.group("away").strip()
        try:
            home_slug = TEAM_SLUGS[home_name]
            away_slug = TEAM_SLUGS[away_name]
        except KeyError as error:
            raise ValueError(
                f"Unknown team {error.args[0]!r} on line {line_number}"
            ) from error

        kickoff_time = datetime.strptime(current_time, "%H:%M").time()
        kickoff_at = datetime.combine(
            current_date.date(),
            kickoff_time,
            tzinfo=london,
        )
        home_score = int(result.group("home_score"))
        away_score = int(result.group("away_score"))
        matches.append(
            {
                "source_match_id": source_match_id(
                    current_matchweek,
                    home_slug,
                    away_slug,
                ),
                "matchweek": current_matchweek,
                "kickoff_at": kickoff_at.isoformat(),
                "home_team": home_name,
                "home_slug": home_slug,
                "away_team": away_name,
                "away_slug": away_slug,
                "home_score": home_score,
                "away_score": away_score,
            }
        )

    return matches


def validate_results(matches: list[dict[str, object]]) -> None:
    if len(matches) != 380:
        raise ValueError(f"Expected 380 matches, found {len(matches)}")

    source_ids = [str(match["source_match_id"]) for match in matches]
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("Source match identifiers must be unique")

    matchweeks = Counter(int(match["matchweek"]) for match in matches)
    if matchweeks != Counter({matchweek: 10 for matchweek in range(1, 39)}):
        raise ValueError("Each matchweek must contain exactly 10 matches")

    club_matches: defaultdict[str, int] = defaultdict(int)
    club_goals_for: defaultdict[str, int] = defaultdict(int)
    club_goals_against: defaultdict[str, int] = defaultdict(int)
    for match in matches:
        home_slug = str(match["home_slug"])
        away_slug = str(match["away_slug"])
        home_score = int(match["home_score"])
        away_score = int(match["away_score"])
        club_matches[home_slug] += 1
        club_matches[away_slug] += 1
        club_goals_for[home_slug] += home_score
        club_goals_for[away_slug] += away_score
        club_goals_against[home_slug] += away_score
        club_goals_against[away_slug] += home_score

    expected_slugs = set(TEAM_SLUGS.values())
    if set(club_matches) != expected_slugs:
        raise ValueError("Snapshot team set does not match the 20-club mapping")
    if any(total != 38 for total in club_matches.values()):
        raise ValueError("Every club must have exactly 38 matches")
    if sum(club_goals_for.values()) != 1115:
        raise ValueError("Expected 1115 team goals in the 2024-25 season")
    if sum(club_goals_for.values()) != sum(club_goals_against.values()):
        raise ValueError("League goals for and against must balance")


def build_snapshot(source_text: str) -> dict[str, object]:
    matches = parse_results(source_text)
    validate_results(matches)

    home_wins = sum(
        int(match["home_score"]) > int(match["away_score"])
        for match in matches
    )
    draws = sum(
        int(match["home_score"]) == int(match["away_score"])
        for match in matches
    )
    goals = sum(
        int(match["home_score"]) + int(match["away_score"])
        for match in matches
    )

    return {
        "schema_version": 1,
        "source": {
            "name": "OpenFootball English Results",
            "repository_url": SOURCE_REPOSITORY,
            "data_url": SOURCE_URL,
            "raw_url": RAW_URL,
            "license_name": "CC0 1.0 Universal",
            "license_url": LICENSE_URL,
            "source_commit": SOURCE_COMMIT,
            "source_commit_date": "2026-07-31",
        },
        "competition": COMPETITION,
        "season": SEASON,
        "snapshot_date": "2025-05-25",
        "summary": {
            "matches": len(matches),
            "goals": goals,
            "home_wins": home_wins,
            "draws": draws,
            "away_wins": len(matches) - home_wins - draws,
        },
        "matches": matches,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=RAW_URL,
        help="OpenFootball result file path or pinned raw URL",
    )
    parser.add_argument(
        "--output",
        default="data/processed/openfootball_pl_2024_25.json",
        help="Output JSON path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot = build_snapshot(read_text(args.input))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = snapshot["summary"]
    print(
        f"Wrote {summary['matches']} matches and {summary['goals']} goals "
        f"for {SEASON} to {output}"
    )


if __name__ == "__main__":
    main()
