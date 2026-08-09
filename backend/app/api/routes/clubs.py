from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database.seed import MATCH_SOURCE_KIND, SAMPLE_SEASON
from app.database.session import get_db
from app.models import Club, Match, Player
from app.schemas.club import (
    ClubDetail,
    ClubListData,
    ClubMatchPreview,
    ClubSummary,
    PlayerSummary,
    StadiumData,
)
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/clubs", tags=["clubs"])

CLUB_SOURCE_NAME = "Premier League 2024/25 table"
CLUB_SOURCE_URL = (
    "https://www.premierleague.com/en/tables/premier-league/"
    "2024-25/all-matchweeks"
)
SAMPLE_NOTICE = (
    "当前返回 2024-25 赛季完整 20 队与球场地理参考；"
    "球员阵容仍为 12 人样例，不代表当前实时名单。"
)


def to_club_summary(club: Club) -> ClubSummary:
    return ClubSummary(
        id=club.id,
        name=club.name,
        short_name=club.short_name,
        slug=club.slug,
        city=club.city,
        stadium=StadiumData(
            name=club.stadium_name,
            latitude=club.stadium_latitude,
            longitude=club.stadium_longitude,
        ),
        founded_year=club.founded_year,
        primary_color=club.primary_color,
        source_kind=club.source_kind,
    )


def to_match_preview(match: Match) -> ClubMatchPreview | None:
    if (
        match.source_match_id is None
        or match.source_kind != MATCH_SOURCE_KIND
    ):
        return None
    return ClubMatchPreview(
        source_match_id=match.source_match_id,
        season=match.season,
        kickoff_at=match.kickoff_at,
        home_club_name=match.home_club.short_name,
        home_club_slug=match.home_club.slug,
        home_score=match.home_score or 0,
        away_club_name=match.away_club.short_name,
        away_club_slug=match.away_club.slug,
        away_score=match.away_score or 0,
        venue=match.venue,
    )


@router.get("", response_model=ApiResponse[ClubListData])
def list_clubs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ApiResponse[ClubListData]:
    clubs = db.scalars(
        select(Club).order_by(Club.name).offset(offset).limit(limit)
    ).all()
    total = db.scalar(select(func.count(Club.id))) or 0
    player_total = db.scalar(select(func.count(Player.id))) or 0

    return ApiResponse(
        message="球队列表获取成功",
        data=ClubListData(
            items=[to_club_summary(club) for club in clubs],
            total=total,
            player_total=player_total,
            limit=limit,
            offset=offset,
            season=SAMPLE_SEASON,
            is_complete=total == 20,
            source_name=CLUB_SOURCE_NAME,
            source_url=CLUB_SOURCE_URL,
            sample_notice=SAMPLE_NOTICE,
        ),
    )


@router.get("/{slug}", response_model=ApiResponse[ClubDetail])
def get_club(
    slug: str,
    db: Session = Depends(get_db),
) -> ApiResponse[ClubDetail]:
    club = db.scalar(
        select(Club)
        .options(
            selectinload(Club.players),
            selectinload(Club.home_matches).selectinload(Match.away_club),
            selectinload(Club.away_matches).selectinload(Match.home_club),
        )
        .where(Club.slug == slug)
    )
    if club is None:
        raise HTTPException(status_code=404, detail="未找到该球队")

    summary = to_club_summary(club)
    match_previews = [
        preview
        for preview in (
            to_match_preview(match)
            for match in [*club.home_matches, *club.away_matches]
        )
        if preview is not None
    ]
    return ApiResponse(
        message="球队详情获取成功",
        data=ClubDetail(
            **summary.model_dump(),
            players=[
                PlayerSummary.model_validate(player)
                for player in sorted(
                    club.players,
                    key=lambda item: (
                        item.position,
                        item.shirt_number or 999,
                        item.full_name,
                    ),
                )
            ],
            featured_matches=sorted(
                match_previews,
                key=lambda item: (
                    item.kickoff_at.isoformat()
                    if item.kickoff_at is not None
                    else ""
                ),
                reverse=True,
            ),
        ),
    )
