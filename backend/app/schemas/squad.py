from typing import Literal

from pydantic import BaseModel


SquadPosition = Literal["GK", "DEF", "MID", "FWD"]
SquadLeaderMetric = Literal[
    "minutes",
    "goals",
    "assists",
    "key_passes",
    "defensive_actions",
]


class SquadClubData(BaseModel):
    id: int
    name: str
    short_name: str
    slug: str
    primary_color: str


class SquadPlayerData(BaseModel):
    full_name: str
    slug: str
    position: SquadPosition
    nationality: str
    appearances: int
    starts: int
    minutes: int
    goals: int
    assists: int
    minutes_share: float


class SquadPositionGroup(BaseModel):
    position: SquadPosition
    label: str
    record_count: int
    minutes: int
    minutes_share: float
    goals: int
    assists: int
    goal_contributions: int


class SquadLeaderData(BaseModel):
    metric: SquadLeaderMetric
    label: str
    value: int
    unit: str
    player: SquadPlayerData


class SquadLensData(BaseModel):
    club: SquadClubData
    season: str
    minimum_minutes: int
    record_total: int
    qualified_total: int
    excluded_total: int
    total_minutes: int
    total_goals: int
    total_assists: int
    unique_nationalities: int
    top_five_minutes_share: float
    position_groups: list[SquadPositionGroup]
    leaders: list[SquadLeaderData]
    core_players: list[SquadPlayerData]
    summary: list[str]
    source_name: str
    source_url: str
    source_version: int
    license_name: str
    license_url: str
    sample_notice: str
    method_notice: str
