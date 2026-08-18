from typing import Literal

from pydantic import BaseModel


TransferPosition = Literal["GK", "DEF", "MID", "FWD"]
TransferMetricKey = Literal[
    "goals_per90",
    "assists_per90",
    "shots_per90",
    "key_passes_per90",
    "tackles_per90",
    "interceptions_per90",
    "expected_goals_per90",
]


class TransferClubData(BaseModel):
    name: str
    short_name: str
    slug: str
    primary_color: str


class TransferNeedMetric(BaseModel):
    key: TransferMetricKey
    label: str
    club_percentile: int
    priority: int


class TransferMetricGap(BaseModel):
    key: TransferMetricKey
    label: str
    club_percentile: int
    candidate_percentile: int
    gap: int


class TransferCandidateData(BaseModel):
    full_name: str
    slug: str
    position: TransferPosition
    nationality: str
    birth_year: int | None
    club: TransferClubData
    appearances: int
    minutes: int
    signal_score: int
    confidence_score: int
    key_lifts: list[TransferMetricGap]
    tradeoffs: list[TransferMetricGap]


class TransferSignalData(BaseModel):
    club: TransferClubData
    season: str
    position: TransferPosition
    minimum_minutes: int
    limit: int
    is_supported: bool
    unavailable_reason: str | None
    club_record_count: int
    peer_record_count: int
    candidate_total: int
    needs: list[TransferNeedMetric]
    candidates: list[TransferCandidateData]
    source_name: str
    source_url: str
    source_version: int
    license_name: str
    license_url: str
    sample_notice: str
    method_notice: str
    decision_notice: str
