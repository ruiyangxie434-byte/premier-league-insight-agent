from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.database.seed import (
    SAMPLE_SEASON,
    SEASON_RESULTS_SOURCE_KIND,
    load_season_results_snapshot,
)
from app.database.session import get_db
from app.models import Club, Match, Standing
from app.schemas.common import ApiResponse
from app.schemas.form import (
    ClubSeasonFormData,
    SeasonFormClubItem,
    SeasonFormOverviewData,
)
from app.services.season_form import (
    build_record,
    chronological,
    club_match_data,
    form_club,
    longest_unbeaten_run,
    points_by_matchweek,
    recent_form,
    result_for_club,
)

router = APIRouter(prefix="/form", tags=["season form"])

FORM_SNAPSHOT = load_season_results_snapshot()
FORM_SOURCE = FORM_SNAPSHOT["source"]
FORM_NOTICE = (
    "本页是 2024-25 已完赛历史比分快照，不是实时赛程；"
    "状态和积分走势只由最终比分计算，不推断 xG、控球率或比赛过程。"
)


def season_result_query(season: str):
    return (
        select(Match)
        .options(
            selectinload(Match.home_club),
            selectinload(Match.away_club),
        )
        .where(
            Match.season == season,
            Match.source_kind == SEASON_RESULTS_SOURCE_KIND,
        )
        .order_by(Match.kickoff_at, Match.matchweek, Match.id)
    )


def source_fields() -> dict[str, str]:
    return {
        "source_name": FORM_SOURCE["name"],
        "source_url": FORM_SOURCE["data_url"],
        "license_name": FORM_SOURCE["license_name"],
        "license_url": FORM_SOURCE["license_url"],
        "source_commit": FORM_SOURCE["source_commit"],
        "sample_notice": FORM_NOTICE,
    }


def require_supported_season(season: str) -> None:
    if season != FORM_SNAPSHOT["season"]:
        raise HTTPException(
            status_code=404,
            detail="当前仅提供 2024-25 赛季完整赛果快照",
        )


@router.get("", response_model=ApiResponse[SeasonFormOverviewData])
def get_season_form(
    season: str = Query(default=SAMPLE_SEASON, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
) -> ApiResponse[SeasonFormOverviewData]:
    require_supported_season(season)
    matches = list(db.scalars(season_result_query(season)).all())
    standings = list(
        db.scalars(
            select(Standing)
            .options(selectinload(Standing.club))
            .where(Standing.season == season)
            .order_by(Standing.position)
        ).all()
    )
    if len(matches) != 380 or len(standings) != 20:
        raise HTTPException(status_code=503, detail="赛季结果快照尚未完整初始化")

    items: list[SeasonFormClubItem] = []
    for standing in standings:
        club_matches = [
            match
            for match in matches
            if standing.club_id in (match.home_club_id, match.away_club_id)
        ]
        form = recent_form(club_matches, standing.club_id)
        items.append(
            SeasonFormClubItem(
                position=standing.position,
                club=form_club(standing.club),
                overall=build_record(club_matches, standing.club_id),
                home=build_record(
                    (
                        match
                        for match in club_matches
                        if match.home_club_id == standing.club_id
                    ),
                    standing.club_id,
                ),
                away=build_record(
                    (
                        match
                        for match in club_matches
                        if match.away_club_id == standing.club_id
                    ),
                    standing.club_id,
                ),
                recent_form=form,
                recent_points=sum(
                    3 if result == "W" else 1 if result == "D" else 0
                    for result in form
                ),
                points_by_matchweek=points_by_matchweek(
                    club_matches,
                    standing.club_id,
                ),
            )
        )

    goal_count = sum(
        (match.home_score or 0) + (match.away_score or 0)
        for match in matches
    )
    home_wins = sum(
        (match.home_score or 0) > (match.away_score or 0)
        for match in matches
    )
    draws = sum(match.home_score == match.away_score for match in matches)
    return ApiResponse(
        message="赛季状态总览获取成功",
        data=SeasonFormOverviewData(
            competition=FORM_SNAPSHOT["competition"],
            season=season,
            snapshot_date=FORM_SNAPSHOT["snapshot_date"],
            match_count=len(matches),
            goal_count=goal_count,
            goals_per_match=round(goal_count / len(matches), 2),
            home_wins=home_wins,
            draws=draws,
            away_wins=len(matches) - home_wins - draws,
            items=items,
            **source_fields(),
        ),
    )


@router.get(
    "/clubs/{slug}",
    response_model=ApiResponse[ClubSeasonFormData],
)
def get_club_season_form(
    slug: str,
    season: str = Query(default=SAMPLE_SEASON, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
) -> ApiResponse[ClubSeasonFormData]:
    require_supported_season(season)
    club = db.scalar(select(Club).where(Club.slug == slug))
    if club is None:
        raise HTTPException(status_code=404, detail="未找到该球队")
    standing = db.scalar(
        select(Standing).where(
            Standing.club_id == club.id,
            Standing.season == season,
        )
    )
    matches = list(
        db.scalars(
            season_result_query(season).where(
                or_(
                    Match.home_club_id == club.id,
                    Match.away_club_id == club.id,
                )
            )
        ).all()
    )
    if standing is None or len(matches) != 38:
        raise HTTPException(status_code=503, detail="球队赛季结果尚未完整初始化")

    ordered = chronological(matches)
    return ApiResponse(
        message="球队赛季状态获取成功",
        data=ClubSeasonFormData(
            competition=FORM_SNAPSHOT["competition"],
            season=season,
            snapshot_date=FORM_SNAPSHOT["snapshot_date"],
            club=form_club(club),
            final_position=standing.position,
            overall=build_record(matches, club.id),
            home=build_record(
                (match for match in matches if match.home_club_id == club.id),
                club.id,
            ),
            away=build_record(
                (match for match in matches if match.away_club_id == club.id),
                club.id,
            ),
            recent_form=recent_form(matches, club.id),
            longest_unbeaten=longest_unbeaten_run(matches, club.id),
            points_by_matchweek=points_by_matchweek(matches, club.id),
            matches=[club_match_data(match, club.id) for match in ordered],
            **source_fields(),
        ),
    )
