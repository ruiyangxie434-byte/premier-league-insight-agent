from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class StadiumData(BaseModel):
    name: str
    latitude: float
    longitude: float


class ClubSummary(BaseModel):
    id: int
    name: str
    short_name: str
    slug: str
    city: str
    stadium: StadiumData
    founded_year: int | None
    primary_color: str
    source_kind: str


class PlayerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    slug: str
    shirt_number: int | None
    position: str
    nationality: str
    date_of_birth: date | None
    birth_year: int | None
    source_kind: str


class ClubMatchPreview(BaseModel):
    source_match_id: str
    season: str
    kickoff_at: datetime | None
    home_club_name: str
    home_club_slug: str
    home_score: int
    away_club_name: str
    away_club_slug: str
    away_score: int
    venue: str


class ClubDetail(ClubSummary):
    players: list[PlayerSummary]
    featured_matches: list[ClubMatchPreview]


class ClubListData(BaseModel):
    items: list[ClubSummary]
    total: int
    player_total: int
    limit: int
    offset: int
    season: str
    is_complete: bool
    source_name: str
    source_url: str
    sample_notice: str
