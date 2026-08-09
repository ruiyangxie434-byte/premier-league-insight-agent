import json
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Club, Match, MatchEvent, Player, PlayerSeasonStat, Standing

SAMPLE_SEASON = "2024-25"
CLUB_SOURCE_KIND = "reference"
STANDING_SOURCE_KIND = "historical"
PLAYER_SOURCE_KIND = "sample"
MATCH_SOURCE_KIND = "open-data"
SEASON_RESULTS_SOURCE_KIND = "openfootball"
MATCH_SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "statsbomb_match_3749448.json"
)
SEASON_RESULTS_SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "openfootball_pl_2024_25.json"
)

CLUBS = [
    {
        "name": "Arsenal",
        "short_name": "Arsenal",
        "slug": "arsenal",
        "city": "London",
        "stadium_name": "Emirates Stadium",
        "stadium_latitude": 51.5549,
        "stadium_longitude": -0.1084,
        "founded_year": 1886,
        "primary_color": "#ef0107",
    },
    {
        "name": "Aston Villa",
        "short_name": "Aston Villa",
        "slug": "aston-villa",
        "city": "Birmingham",
        "stadium_name": "Villa Park",
        "stadium_latitude": 52.5085,
        "stadium_longitude": -1.8849,
        "founded_year": 1874,
        "primary_color": "#670e36",
    },
    {
        "name": "AFC Bournemouth",
        "short_name": "Bournemouth",
        "slug": "bournemouth",
        "city": "Bournemouth",
        "stadium_name": "Vitality Stadium",
        "stadium_latitude": 50.7352,
        "stadium_longitude": -1.8383,
        "founded_year": 1899,
        "primary_color": "#da291c",
    },
    {
        "name": "Brentford",
        "short_name": "Brentford",
        "slug": "brentford",
        "city": "London",
        "stadium_name": "Gtech Community Stadium",
        "stadium_latitude": 51.4908,
        "stadium_longitude": -0.2887,
        "founded_year": 1889,
        "primary_color": "#e30613",
    },
    {
        "name": "Brighton & Hove Albion",
        "short_name": "Brighton",
        "slug": "brighton-and-hove-albion",
        "city": "Brighton",
        "stadium_name": "Amex Stadium",
        "stadium_latitude": 50.8616,
        "stadium_longitude": -0.0837,
        "founded_year": 1901,
        "primary_color": "#0057b8",
    },
    {
        "name": "Chelsea",
        "short_name": "Chelsea",
        "slug": "chelsea",
        "city": "London",
        "stadium_name": "Stamford Bridge",
        "stadium_latitude": 51.4817,
        "stadium_longitude": -0.1910,
        "founded_year": 1905,
        "primary_color": "#034694",
    },
    {
        "name": "Crystal Palace",
        "short_name": "Crystal Palace",
        "slug": "crystal-palace",
        "city": "London",
        "stadium_name": "Selhurst Park",
        "stadium_latitude": 51.3983,
        "stadium_longitude": -0.0856,
        "founded_year": 1905,
        "primary_color": "#1b458f",
    },
    {
        "name": "Everton",
        "short_name": "Everton",
        "slug": "everton",
        "city": "Liverpool",
        "stadium_name": "Goodison Park",
        "stadium_latitude": 53.4388,
        "stadium_longitude": -2.9664,
        "founded_year": 1878,
        "primary_color": "#003399",
    },
    {
        "name": "Fulham",
        "short_name": "Fulham",
        "slug": "fulham",
        "city": "London",
        "stadium_name": "Craven Cottage",
        "stadium_latitude": 51.4749,
        "stadium_longitude": -0.2217,
        "founded_year": 1879,
        "primary_color": "#111111",
    },
    {
        "name": "Ipswich Town",
        "short_name": "Ipswich",
        "slug": "ipswich-town",
        "city": "Ipswich",
        "stadium_name": "Portman Road",
        "stadium_latitude": 52.0550,
        "stadium_longitude": 1.1448,
        "founded_year": 1878,
        "primary_color": "#3a64a3",
    },
    {
        "name": "Leicester City",
        "short_name": "Leicester",
        "slug": "leicester-city",
        "city": "Leicester",
        "stadium_name": "King Power Stadium",
        "stadium_latitude": 52.6203,
        "stadium_longitude": -1.1422,
        "founded_year": 1884,
        "primary_color": "#003090",
    },
    {
        "name": "Liverpool",
        "short_name": "Liverpool",
        "slug": "liverpool",
        "city": "Liverpool",
        "stadium_name": "Anfield",
        "stadium_latitude": 53.4308,
        "stadium_longitude": -2.9608,
        "founded_year": 1892,
        "primary_color": "#c8102e",
    },
    {
        "name": "Manchester City",
        "short_name": "Man City",
        "slug": "manchester-city",
        "city": "Manchester",
        "stadium_name": "Etihad Stadium",
        "stadium_latitude": 53.4831,
        "stadium_longitude": -2.2004,
        "founded_year": 1880,
        "primary_color": "#6cabdd",
    },
    {
        "name": "Manchester United",
        "short_name": "Man United",
        "slug": "manchester-united",
        "city": "Manchester",
        "stadium_name": "Old Trafford",
        "stadium_latitude": 53.4631,
        "stadium_longitude": -2.2913,
        "founded_year": 1878,
        "primary_color": "#da291c",
    },
    {
        "name": "Newcastle United",
        "short_name": "Newcastle",
        "slug": "newcastle-united",
        "city": "Newcastle upon Tyne",
        "stadium_name": "St James' Park",
        "stadium_latitude": 54.9752,
        "stadium_longitude": -1.6224,
        "founded_year": 1892,
        "primary_color": "#f1be48",
    },
    {
        "name": "Nottingham Forest",
        "short_name": "Nott'm Forest",
        "slug": "nottingham-forest",
        "city": "Nottingham",
        "stadium_name": "City Ground",
        "stadium_latitude": 52.9400,
        "stadium_longitude": -1.1327,
        "founded_year": 1865,
        "primary_color": "#dd0000",
    },
    {
        "name": "Southampton",
        "short_name": "Southampton",
        "slug": "southampton",
        "city": "Southampton",
        "stadium_name": "St Mary's Stadium",
        "stadium_latitude": 50.9058,
        "stadium_longitude": -1.3911,
        "founded_year": 1885,
        "primary_color": "#d71920",
    },
    {
        "name": "Tottenham Hotspur",
        "short_name": "Tottenham",
        "slug": "tottenham-hotspur",
        "city": "London",
        "stadium_name": "Tottenham Hotspur Stadium",
        "stadium_latitude": 51.6043,
        "stadium_longitude": -0.0665,
        "founded_year": 1882,
        "primary_color": "#132257",
    },
    {
        "name": "West Ham United",
        "short_name": "West Ham",
        "slug": "west-ham-united",
        "city": "London",
        "stadium_name": "London Stadium",
        "stadium_latitude": 51.5386,
        "stadium_longitude": -0.0165,
        "founded_year": 1895,
        "primary_color": "#7a263a",
    },
    {
        "name": "Wolverhampton Wanderers",
        "short_name": "Wolves",
        "slug": "wolverhampton-wanderers",
        "city": "Wolverhampton",
        "stadium_name": "Molineux Stadium",
        "stadium_latitude": 52.5903,
        "stadium_longitude": -2.1304,
        "founded_year": 1877,
        "primary_color": "#fdb913",
    },
]

STANDINGS = {
    "liverpool": {
        "position": 1,
        "played": 38,
        "won": 25,
        "drawn": 9,
        "lost": 4,
        "goals_for": 86,
        "goals_against": 41,
        "points": 84,
    },
    "arsenal": {
        "position": 2,
        "played": 38,
        "won": 20,
        "drawn": 14,
        "lost": 4,
        "goals_for": 69,
        "goals_against": 34,
        "points": 74,
    },
    "manchester-city": {
        "position": 3,
        "played": 38,
        "won": 21,
        "drawn": 8,
        "lost": 9,
        "goals_for": 72,
        "goals_against": 44,
        "points": 71,
    },
    "chelsea": {
        "position": 4,
        "played": 38,
        "won": 20,
        "drawn": 9,
        "lost": 9,
        "goals_for": 64,
        "goals_against": 43,
        "points": 69,
    },
    "newcastle-united": {
        "position": 5,
        "played": 38,
        "won": 20,
        "drawn": 6,
        "lost": 12,
        "goals_for": 68,
        "goals_against": 47,
        "points": 66,
    },
    "aston-villa": {
        "position": 6,
        "played": 38,
        "won": 19,
        "drawn": 9,
        "lost": 10,
        "goals_for": 58,
        "goals_against": 51,
        "points": 66,
    },
    "nottingham-forest": {
        "position": 7,
        "played": 38,
        "won": 19,
        "drawn": 8,
        "lost": 11,
        "goals_for": 58,
        "goals_against": 46,
        "points": 65,
    },
    "brighton-and-hove-albion": {
        "position": 8,
        "played": 38,
        "won": 16,
        "drawn": 13,
        "lost": 9,
        "goals_for": 66,
        "goals_against": 59,
        "points": 61,
    },
    "bournemouth": {
        "position": 9,
        "played": 38,
        "won": 15,
        "drawn": 11,
        "lost": 12,
        "goals_for": 58,
        "goals_against": 46,
        "points": 56,
    },
    "brentford": {
        "position": 10,
        "played": 38,
        "won": 16,
        "drawn": 8,
        "lost": 14,
        "goals_for": 66,
        "goals_against": 57,
        "points": 56,
    },
    "fulham": {
        "position": 11,
        "played": 38,
        "won": 15,
        "drawn": 9,
        "lost": 14,
        "goals_for": 54,
        "goals_against": 54,
        "points": 54,
    },
    "crystal-palace": {
        "position": 12,
        "played": 38,
        "won": 13,
        "drawn": 14,
        "lost": 11,
        "goals_for": 51,
        "goals_against": 51,
        "points": 53,
    },
    "everton": {
        "position": 13,
        "played": 38,
        "won": 11,
        "drawn": 15,
        "lost": 12,
        "goals_for": 42,
        "goals_against": 44,
        "points": 48,
    },
    "west-ham-united": {
        "position": 14,
        "played": 38,
        "won": 11,
        "drawn": 10,
        "lost": 17,
        "goals_for": 46,
        "goals_against": 62,
        "points": 43,
    },
    "manchester-united": {
        "position": 15,
        "played": 38,
        "won": 11,
        "drawn": 9,
        "lost": 18,
        "goals_for": 44,
        "goals_against": 54,
        "points": 42,
    },
    "wolverhampton-wanderers": {
        "position": 16,
        "played": 38,
        "won": 12,
        "drawn": 6,
        "lost": 20,
        "goals_for": 54,
        "goals_against": 69,
        "points": 42,
    },
    "tottenham-hotspur": {
        "position": 17,
        "played": 38,
        "won": 11,
        "drawn": 5,
        "lost": 22,
        "goals_for": 64,
        "goals_against": 65,
        "points": 38,
    },
    "leicester-city": {
        "position": 18,
        "played": 38,
        "won": 6,
        "drawn": 7,
        "lost": 25,
        "goals_for": 33,
        "goals_against": 80,
        "points": 25,
    },
    "ipswich-town": {
        "position": 19,
        "played": 38,
        "won": 4,
        "drawn": 10,
        "lost": 24,
        "goals_for": 36,
        "goals_against": 82,
        "points": 22,
    },
    "southampton": {
        "position": 20,
        "played": 38,
        "won": 2,
        "drawn": 6,
        "lost": 30,
        "goals_for": 26,
        "goals_against": 86,
        "points": 12,
    },
}

PLAYERS = {
    "liverpool": [
        {
            "full_name": "Mohamed Salah",
            "slug": "mohamed-salah",
            "shirt_number": 11,
            "position": "FWD",
            "nationality": "Egypt",
            "date_of_birth": date(1992, 6, 15),
            "stats": {
                "appearances": 38,
                "starts": 38,
                "minutes": 3378,
                "goals": 29,
                "assists": 18,
                "shots": 130,
                "key_passes": 88,
                "tackles": 19,
                "interceptions": 4,
                "expected_goals": 25.2,
            },
        },
        {
            "full_name": "Virgil van Dijk",
            "slug": "virgil-van-dijk",
            "shirt_number": 4,
            "position": "DEF",
            "nationality": "Netherlands",
            "date_of_birth": date(1991, 7, 8),
            "stats": {
                "appearances": 37,
                "starts": 37,
                "minutes": 3330,
                "goals": 3,
                "assists": 1,
                "shots": 27,
                "key_passes": 10,
                "tackles": 36,
                "interceptions": 40,
                "expected_goals": 3.6,
            },
        },
    ],
    "arsenal": [
        {
            "full_name": "Bukayo Saka",
            "slug": "bukayo-saka",
            "shirt_number": 7,
            "position": "FWD",
            "nationality": "England",
            "date_of_birth": date(2001, 9, 5),
            "stats": {
                "appearances": 25,
                "starts": 24,
                "minutes": 2100,
                "goals": 6,
                "assists": 10,
                "shots": 63,
                "key_passes": 61,
                "tackles": 22,
                "interceptions": 9,
                "expected_goals": 8.4,
            },
        },
        {
            "full_name": "Declan Rice",
            "slug": "declan-rice",
            "shirt_number": 41,
            "position": "MID",
            "nationality": "England",
            "date_of_birth": date(1999, 1, 14),
            "stats": {
                "appearances": 35,
                "starts": 34,
                "minutes": 2957,
                "goals": 4,
                "assists": 8,
                "shots": 42,
                "key_passes": 54,
                "tackles": 58,
                "interceptions": 31,
                "expected_goals": 3.4,
            },
        },
    ],
    "manchester-city": [
        {
            "full_name": "Erling Haaland",
            "slug": "erling-haaland",
            "shirt_number": 9,
            "position": "FWD",
            "nationality": "Norway",
            "date_of_birth": date(2000, 7, 21),
            "stats": {
                "appearances": 31,
                "starts": 31,
                "minutes": 2767,
                "goals": 22,
                "assists": 3,
                "shots": 107,
                "key_passes": 19,
                "tackles": 8,
                "interceptions": 2,
                "expected_goals": 22.1,
            },
        },
        {
            "full_name": "Phil Foden",
            "slug": "phil-foden",
            "shirt_number": 47,
            "position": "MID",
            "nationality": "England",
            "date_of_birth": date(2000, 5, 28),
            "stats": {
                "appearances": 28,
                "starts": 20,
                "minutes": 1800,
                "goals": 7,
                "assists": 2,
                "shots": 58,
                "key_passes": 39,
                "tackles": 20,
                "interceptions": 10,
                "expected_goals": 7.2,
            },
        },
    ],
    "chelsea": [
        {
            "full_name": "Cole Palmer",
            "slug": "cole-palmer",
            "shirt_number": 20,
            "position": "FWD",
            "nationality": "England",
            "date_of_birth": date(2002, 5, 6),
            "stats": {
                "appearances": 37,
                "starts": 36,
                "minutes": 3180,
                "goals": 15,
                "assists": 8,
                "shots": 112,
                "key_passes": 89,
                "tackles": 27,
                "interceptions": 11,
                "expected_goals": 14.8,
            },
        },
        {
            "full_name": "Moises Caicedo",
            "slug": "moises-caicedo",
            "shirt_number": 25,
            "position": "MID",
            "nationality": "Ecuador",
            "date_of_birth": date(2001, 11, 2),
            "stats": {
                "appearances": 38,
                "starts": 38,
                "minutes": 3420,
                "goals": 1,
                "assists": 2,
                "shots": 23,
                "key_passes": 31,
                "tackles": 91,
                "interceptions": 52,
                "expected_goals": 1.3,
            },
        },
    ],
    "newcastle-united": [
        {
            "full_name": "Alexander Isak",
            "slug": "alexander-isak",
            "shirt_number": 14,
            "position": "FWD",
            "nationality": "Sweden",
            "date_of_birth": date(1999, 9, 21),
            "stats": {
                "appearances": 34,
                "starts": 34,
                "minutes": 2894,
                "goals": 23,
                "assists": 6,
                "shots": 99,
                "key_passes": 42,
                "tackles": 15,
                "interceptions": 5,
                "expected_goals": 20.3,
            },
        },
        {
            "full_name": "Bruno Guimaraes",
            "slug": "bruno-guimaraes",
            "shirt_number": 39,
            "position": "MID",
            "nationality": "Brazil",
            "date_of_birth": date(1997, 11, 16),
            "stats": {
                "appearances": 38,
                "starts": 37,
                "minutes": 3290,
                "goals": 5,
                "assists": 6,
                "shots": 42,
                "key_passes": 52,
                "tackles": 72,
                "interceptions": 37,
                "expected_goals": 4.2,
            },
        },
    ],
    "aston-villa": [
        {
            "full_name": "Ollie Watkins",
            "slug": "ollie-watkins",
            "shirt_number": 11,
            "position": "FWD",
            "nationality": "England",
            "date_of_birth": date(1995, 12, 30),
            "stats": {
                "appearances": 38,
                "starts": 31,
                "minutes": 2842,
                "goals": 16,
                "assists": 8,
                "shots": 87,
                "key_passes": 38,
                "tackles": 12,
                "interceptions": 4,
                "expected_goals": 15.7,
            },
        },
        {
            "full_name": "Youri Tielemans",
            "slug": "youri-tielemans",
            "shirt_number": 8,
            "position": "MID",
            "nationality": "Belgium",
            "date_of_birth": date(1997, 5, 7),
            "stats": {
                "appearances": 36,
                "starts": 35,
                "minutes": 3105,
                "goals": 3,
                "assists": 7,
                "shots": 48,
                "key_passes": 55,
                "tackles": 56,
                "interceptions": 28,
                "expected_goals": 3.1,
            },
        },
    ],
}


def load_match_snapshot() -> dict:
    return json.loads(MATCH_SNAPSHOT_PATH.read_text(encoding="utf-8"))


def load_season_results_snapshot() -> dict:
    return json.loads(
        SEASON_RESULTS_SNAPSHOT_PATH.read_text(encoding="utf-8")
    )


def seed_season_results(
    session: Session,
    clubs_by_slug: dict[str, Club],
) -> bool:
    """Synchronize the pinned 2024-25 OpenFootball result snapshot."""

    snapshot = load_season_results_snapshot()
    existing_matches = {
        match.source_match_id: match
        for match in session.scalars(
            select(Match).where(
                Match.source_kind == SEASON_RESULTS_SOURCE_KIND
            )
        ).all()
        if match.source_match_id is not None
    }
    rows_changed = False

    for match_data in snapshot["matches"]:
        source_match_id = match_data["source_match_id"]
        kickoff_at = (
            datetime.fromisoformat(match_data["kickoff_at"])
            .astimezone(UTC)
            .replace(tzinfo=None)
        )
        home_club = clubs_by_slug[match_data["home_slug"]]
        away_club = clubs_by_slug[match_data["away_slug"]]
        expected_match = {
            "season": snapshot["season"],
            "matchweek": match_data["matchweek"],
            "kickoff_at": kickoff_at,
            "home_club_id": home_club.id,
            "away_club_id": away_club.id,
            "home_score": match_data["home_score"],
            "away_score": match_data["away_score"],
            "venue": home_club.stadium_name,
            "status": "completed",
            "source_kind": SEASON_RESULTS_SOURCE_KIND,
        }
        match = existing_matches.get(source_match_id)
        if match is None:
            session.add(Match(source_match_id=source_match_id, **expected_match))
            rows_changed = True
            continue

        for field, value in expected_match.items():
            if getattr(match, field) != value:
                setattr(match, field, value)
                rows_changed = True

    return rows_changed


def seed_match_snapshot(
    session: Session,
    clubs_by_slug: dict[str, Club],
) -> bool:
    snapshot = load_match_snapshot()
    match_data = snapshot["match"]
    source_match_id = match_data["source_match_id"]
    kickoff_at = datetime.fromisoformat(
        f"{match_data['match_date']}T{match_data['kick_off']}"
    )
    home_slug = match_data["home_team"].casefold().replace(" ", "-")
    away_slug = match_data["away_team"].casefold().replace(" ", "-")
    home_club = clubs_by_slug[home_slug]
    away_club = clubs_by_slug[away_slug]
    expected_match = {
        "season": match_data["season"],
        "matchweek": match_data["matchweek"],
        "kickoff_at": kickoff_at,
        "home_club_id": home_club.id,
        "away_club_id": away_club.id,
        "home_score": match_data["home_score"],
        "away_score": match_data["away_score"],
        "venue": match_data["venue"],
        "status": match_data["status"],
        "source_kind": MATCH_SOURCE_KIND,
    }

    rows_changed = False
    match = session.scalar(
        select(Match).where(Match.source_match_id == source_match_id)
    )
    if match is None:
        match = Match(source_match_id=source_match_id, **expected_match)
        session.add(match)
        session.flush()
        rows_changed = True
    else:
        for field, value in expected_match.items():
            if getattr(match, field) != value:
                setattr(match, field, value)
                rows_changed = True

    for shot in snapshot["shots"]:
        event = session.scalar(
            select(MatchEvent).where(
                MatchEvent.source_event_id == shot["source_event_id"]
            )
        )
        expected_event = {
            "match_id": match.id,
            "club_id": clubs_by_slug[shot["team_slug"]].id,
            "player_id": None,
            "player_name": shot["player_name"],
            "period": shot["period"],
            "minute": shot["minute"],
            "second": shot["second"],
            "event_type": "shot",
            "outcome": shot["outcome"],
            "x": shot["x"],
            "y": shot["y"],
            "xg": shot["xg"],
            "body_part": shot["body_part"],
            "shot_type": shot["shot_type"],
            "play_pattern": shot["play_pattern"],
            "source_kind": MATCH_SOURCE_KIND,
        }
        if event is None:
            session.add(
                MatchEvent(
                    source_event_id=shot["source_event_id"],
                    **expected_event,
                )
            )
            rows_changed = True
        else:
            for field, value in expected_event.items():
                if getattr(event, field) != value:
                    setattr(event, field, value)
                    rows_changed = True

    return rows_changed


def seed_sample_data(session: Session) -> bool:
    """Synchronize the public demo dataset.

    Club and final-table reference rows are updated in place so an existing
    v0.5 database can receive the complete league without deleting SQLite.
    Player and player-stat rows remain clearly marked as samples.  The complete
    2024-25 result list and featured historical event match are synchronized
    from separate compact snapshots with distinct provenance.
    """

    rows_changed = False
    clubs_by_slug: dict[str, Club] = {}
    for club_data in CLUBS:
        club = session.scalar(select(Club).where(Club.slug == club_data["slug"]))
        if club is None:
            club = Club(**club_data, source_kind=CLUB_SOURCE_KIND)
            session.add(club)
            session.flush()
            rows_changed = True
        else:
            expected_club_data = {
                **club_data,
                "source_kind": CLUB_SOURCE_KIND,
            }
            for field, value in expected_club_data.items():
                if getattr(club, field) != value:
                    setattr(club, field, value)
                    rows_changed = True
        clubs_by_slug[club.slug] = club

    for slug, standing_data in STANDINGS.items():
        standing = session.scalar(
            select(Standing).where(
                Standing.club_id == clubs_by_slug[slug].id,
                Standing.season == SAMPLE_SEASON,
            )
        )
        if standing is None:
            session.add(
                Standing(
                    club_id=clubs_by_slug[slug].id,
                    season=SAMPLE_SEASON,
                    source_kind=STANDING_SOURCE_KIND,
                    **standing_data,
                )
            )
            rows_changed = True
        else:
            expected_standing_data = {
                **standing_data,
                "source_kind": STANDING_SOURCE_KIND,
            }
            for field, value in expected_standing_data.items():
                if getattr(standing, field) != value:
                    setattr(standing, field, value)
                    rows_changed = True

    for slug, players in PLAYERS.items():
        for player_data in players:
            player = session.scalar(
                select(Player).where(Player.slug == player_data["slug"])
            )
            if player is None:
                player = Player(
                    club_id=clubs_by_slug[slug].id,
                    full_name=player_data["full_name"],
                    slug=player_data["slug"],
                    shirt_number=player_data["shirt_number"],
                    position=player_data["position"],
                    nationality=player_data["nationality"],
                    date_of_birth=player_data["date_of_birth"],
                    source_kind=PLAYER_SOURCE_KIND,
                )
                session.add(player)
                session.flush()
                rows_changed = True

            stats = session.scalar(
                select(PlayerSeasonStat).where(
                    PlayerSeasonStat.player_id == player.id,
                    PlayerSeasonStat.season == SAMPLE_SEASON,
                )
            )
            if stats is None:
                session.add(
                    PlayerSeasonStat(
                        player_id=player.id,
                        season=SAMPLE_SEASON,
                        source_kind=PLAYER_SOURCE_KIND,
                        **player_data["stats"],
                    )
                )
                rows_changed = True

    if seed_season_results(session, clubs_by_slug):
        rows_changed = True

    if seed_match_snapshot(session, clubs_by_slug):
        rows_changed = True

    session.commit()
    return rows_changed
