from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


PlayerPosition = Literal["FWD", "MID", "DEF", "GK"]
PlayerPercentileScope = Literal["position_pool", "all_qualified_players"]
PlayerSortOrder = Literal["asc", "desc"]
PlayerSortKey = Literal[
    "full_name",
    "club",
    "position",
    "minutes",
    "goals",
    "assists",
    "goals_per90",
    "assists_per90",
    "shots_per90",
    "key_passes_per90",
    "tackles_per90",
    "interceptions_per90",
    "expected_goals_per90",
]


class PlayerClubData(BaseModel):
    name: str
    short_name: str
    slug: str
    primary_color: str


class PlayerSeasonTotals(BaseModel):
    appearances: int
    starts: int
    minutes: int
    goals: int
    assists: int
    shots: int
    key_passes: int
    tackles: int
    interceptions: int
    expected_goals: float | None


class PlayerPer90Metrics(BaseModel):
    goals_per90: float
    assists_per90: float
    shots_per90: float
    key_passes_per90: float
    tackles_per90: float
    interceptions_per90: float
    expected_goals_per90: float


class PlayerMetricPercentiles(BaseModel):
    goals_per90: int
    assists_per90: int
    shots_per90: int
    key_passes_per90: int
    tackles_per90: int
    interceptions_per90: int
    expected_goals_per90: int


class PlayerPercentileProfile(BaseModel):
    scope: PlayerPercentileScope
    peer_count: int
    metrics: PlayerMetricPercentiles


class PlayerLabItem(BaseModel):
    photo_url: str | None = None
    photo_urls: list[str] = Field(default_factory=list)
    id: int
    full_name: str
    slug: str
    shirt_number: int | None
    position: PlayerPosition
    nationality: str
    date_of_birth: date | None
    birth_year: int | None
    source_kind: str
    club: PlayerClubData
    season: str
    totals: PlayerSeasonTotals
    per90: PlayerPer90Metrics
    percentiles: PlayerPercentileProfile


class PlayerLabData(BaseModel):
    items: list[PlayerLabItem]
    total: int
    pool_total: int
    dataset_total: int
    unique_player_total: int
    transfer_record_total: int
    season: str
    minimum_minutes: int
    limit: int
    offset: int
    sort_by: PlayerSortKey
    order: PlayerSortOrder
    available_positions: list[PlayerPosition]
    available_clubs: list[PlayerClubData]
    source_name: str
    source_url: str
    source_version: int
    license_name: str
    license_url: str
    sample_notice: str
    percentile_notice: str


class PlayerSimilarityMetricWeight(BaseModel):
    key: str
    label: str
    weight: float


class PlayerSimilarityDifference(BaseModel):
    key: str
    label: str
    target_percentile: int
    candidate_percentile: int
    gap: int


class PlayerSimilarityCandidate(BaseModel):
    player: PlayerLabItem
    similarity_score: int
    closest_metrics: list[str]
    key_difference: PlayerSimilarityDifference


class PlayerSimilarityData(BaseModel):
    target: PlayerLabItem
    items: list[PlayerSimilarityCandidate]
    candidate_total: int
    season: str
    minimum_minutes: int
    position: PlayerPosition
    is_supported: bool
    unavailable_reason: str | None
    metric_weights: list[PlayerSimilarityMetricWeight]
    method_notice: str
    sample_notice: str
