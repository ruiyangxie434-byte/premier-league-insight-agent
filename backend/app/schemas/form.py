from datetime import datetime
from typing import Literal

from pydantic import BaseModel

FormResult = Literal["W", "D", "L"]


class FormClubData(BaseModel):
    id: int
    name: str
    short_name: str
    slug: str
    primary_color: str


class FormRecordData(BaseModel):
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    points_per_game: float


class SeasonFormClubItem(BaseModel):
    position: int
    club: FormClubData
    overall: FormRecordData
    home: FormRecordData
    away: FormRecordData
    recent_form: list[FormResult]
    recent_points: int
    points_by_matchweek: list[int]


class SeasonFormOverviewData(BaseModel):
    competition: str
    season: str
    snapshot_date: str
    match_count: int
    goal_count: int
    goals_per_match: float
    home_wins: int
    draws: int
    away_wins: int
    items: list[SeasonFormClubItem]
    source_name: str
    source_url: str
    license_name: str
    license_url: str
    source_commit: str
    sample_notice: str


class ClubFormMatchData(BaseModel):
    source_match_id: str
    matchweek: int
    kickoff_at: datetime | None
    venue: str
    is_home: bool
    opponent: FormClubData
    home_club: FormClubData
    away_club: FormClubData
    home_score: int
    away_score: int
    result: FormResult
    points: int


class ClubSeasonFormData(BaseModel):
    competition: str
    season: str
    snapshot_date: str
    club: FormClubData
    final_position: int
    overall: FormRecordData
    home: FormRecordData
    away: FormRecordData
    recent_form: list[FormResult]
    longest_unbeaten: int
    points_by_matchweek: list[int]
    matches: list[ClubFormMatchData]
    source_name: str
    source_url: str
    license_name: str
    license_url: str
    source_commit: str
    sample_notice: str


class MatchupClubSnapshot(BaseModel):
    club: FormClubData
    final_position: int
    overall: FormRecordData
    home: FormRecordData
    away: FormRecordData
    recent_form: list[FormResult]
    recent_points: int
    longest_unbeaten: int


class MatchupMeetingData(BaseModel):
    source_match_id: str
    matchweek: int
    kickoff_at: datetime | None
    home_club: FormClubData
    away_club: FormClubData
    home_score: int
    away_score: int
    winner_slug: str | None


class MatchupHeadToHeadData(BaseModel):
    meetings: list[MatchupMeetingData]
    club_a_wins: int
    draws: int
    club_b_wins: int
    club_a_goals: int
    club_b_goals: int


class MatchupDimensionData(BaseModel):
    key: str
    label: str
    club_a_value: str
    club_b_value: str
    advantage: Literal["club_a", "club_b", "even"]
    note: str


class ClubMatchupData(BaseModel):
    competition: str
    season: str
    snapshot_date: str
    club_a: MatchupClubSnapshot
    club_b: MatchupClubSnapshot
    head_to_head: MatchupHeadToHeadData
    dimensions: list[MatchupDimensionData]
    summary: list[str]
    source_name: str
    source_url: str
    license_name: str
    license_url: str
    source_commit: str
    sample_notice: str
