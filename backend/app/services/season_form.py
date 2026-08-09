from collections.abc import Iterable

from app.models import Club, Match
from app.schemas.form import (
    ClubFormMatchData,
    FormClubData,
    FormRecordData,
)


def form_club(club: Club) -> FormClubData:
    return FormClubData(
        id=club.id,
        name=club.name,
        short_name=club.short_name,
        slug=club.slug,
        primary_color=club.primary_color,
    )


def result_for_club(match: Match, club_id: int) -> tuple[str, int, int, int]:
    if match.home_score is None or match.away_score is None:
        raise ValueError("Completed season result is missing its score")
    if match.home_club_id == club_id:
        goals_for, goals_against = match.home_score, match.away_score
    elif match.away_club_id == club_id:
        goals_for, goals_against = match.away_score, match.home_score
    else:
        raise ValueError("Club does not participate in this match")

    if goals_for > goals_against:
        return "W", 3, goals_for, goals_against
    if goals_for == goals_against:
        return "D", 1, goals_for, goals_against
    return "L", 0, goals_for, goals_against


def build_record(matches: Iterable[Match], club_id: int) -> FormRecordData:
    won = drawn = lost = goals_for = goals_against = points = 0
    played = 0
    for match in matches:
        result, match_points, scored, conceded = result_for_club(match, club_id)
        played += 1
        won += result == "W"
        drawn += result == "D"
        lost += result == "L"
        goals_for += scored
        goals_against += conceded
        points += match_points

    return FormRecordData(
        played=played,
        won=won,
        drawn=drawn,
        lost=lost,
        goals_for=goals_for,
        goals_against=goals_against,
        goal_difference=goals_for - goals_against,
        points=points,
        points_per_game=round(points / played, 2) if played else 0,
    )


def chronological(matches: Iterable[Match]) -> list[Match]:
    return sorted(
        matches,
        key=lambda match: (
            match.kickoff_at.isoformat() if match.kickoff_at else "",
            match.matchweek,
            match.id,
        ),
    )


def recent_form(matches: Iterable[Match], club_id: int, limit: int = 5) -> list[str]:
    ordered = chronological(matches)
    return [result_for_club(match, club_id)[0] for match in ordered[-limit:]]


def points_by_matchweek(matches: Iterable[Match], club_id: int) -> list[int]:
    matchweek_points = {
        match.matchweek: result_for_club(match, club_id)[1]
        for match in matches
    }
    cumulative = 0
    timeline: list[int] = []
    for matchweek in range(1, 39):
        cumulative += matchweek_points.get(matchweek, 0)
        timeline.append(cumulative)
    return timeline


def longest_unbeaten_run(matches: Iterable[Match], club_id: int) -> int:
    longest = current = 0
    for match in chronological(matches):
        result = result_for_club(match, club_id)[0]
        if result == "L":
            current = 0
            continue
        current += 1
        longest = max(longest, current)
    return longest


def club_match_data(match: Match, club_id: int) -> ClubFormMatchData:
    if match.source_match_id is None:
        raise ValueError("Season result is missing its source identifier")
    result, points, _, _ = result_for_club(match, club_id)
    is_home = match.home_club_id == club_id
    opponent = match.away_club if is_home else match.home_club
    return ClubFormMatchData(
        source_match_id=match.source_match_id,
        matchweek=match.matchweek,
        kickoff_at=match.kickoff_at,
        venue=match.venue,
        is_home=is_home,
        opponent=form_club(opponent),
        home_club=form_club(match.home_club),
        away_club=form_club(match.away_club),
        home_score=match.home_score or 0,
        away_score=match.away_score or 0,
        result=result,
        points=points,
    )
