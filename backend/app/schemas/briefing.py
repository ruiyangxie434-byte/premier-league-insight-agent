from typing import Literal

from pydantic import BaseModel

from app.schemas.form import FormRecordData, FormResult
from app.schemas.squad import SquadLensData
from app.schemas.transfer import TransferCandidateData, TransferNeedMetric


BriefingPosition = Literal["DEF", "MID", "FWD"]


class BriefingClubData(BaseModel):
    id: int
    name: str
    short_name: str
    slug: str
    city: str
    stadium_name: str
    founded_year: int | None
    primary_color: str


class BriefingSeasonData(BaseModel):
    final_position: int
    overall: FormRecordData
    home: FormRecordData
    away: FormRecordData
    recent_form: list[FormResult]
    recent_points: int
    longest_unbeaten: int


class BriefingRecruitmentData(BaseModel):
    position: BriefingPosition
    label: str
    club_record_count: int
    peer_record_count: int
    candidate_total: int
    needs: list[TransferNeedMetric]
    top_candidate: TransferCandidateData | None
    note: str


class BriefingSourceData(BaseModel):
    name: str
    url: str
    license_name: str | None
    license_url: str | None
    scope: str


class ClubBriefingData(BaseModel):
    club: BriefingClubData
    competition: str
    season: str
    snapshot_date: str
    minimum_minutes: int
    season_summary: BriefingSeasonData
    squad: SquadLensData
    recruitment: list[BriefingRecruitmentData]
    headlines: list[str]
    sources: list[BriefingSourceData]
    limitations: list[str]
    print_notice: str
