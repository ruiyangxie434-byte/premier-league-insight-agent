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
    ClubMatchupData,
    ClubSeasonFormData,
    MatchupClubSnapshot,
    MatchupDimensionData,
    MatchupHeadToHeadData,
    MatchupMeetingData,
    SeasonFormClubItem,
    SeasonFormOverviewData,
    SeasonTimelineData,
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
from app.services.season_timeline import (
    SeasonTimelineUnavailable,
    get_season_timeline,
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


@router.get("/timeline", response_model=ApiResponse[SeasonTimelineData])
def get_timeline(
    season: str = Query(default=SAMPLE_SEASON, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
) -> ApiResponse[SeasonTimelineData]:
    require_supported_season(season)
    try:
        data = get_season_timeline(db, season=season)
    except SeasonTimelineUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ApiResponse(message="赛季时间轴获取成功", data=data)


def matchup_snapshot(
    club: Club,
    standing: Standing,
    matches: list[Match],
) -> MatchupClubSnapshot:
    form = recent_form(matches, club.id)
    return MatchupClubSnapshot(
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
        recent_form=form,
        recent_points=sum(3 if result == "W" else 1 if result == "D" else 0 for result in form),
        longest_unbeaten=longest_unbeaten_run(matches, club.id),
    )


def advantage(left: float, right: float, lower_is_better: bool = False) -> str:
    if left == right:
        return "even"
    left_is_better = left < right if lower_is_better else left > right
    return "club_a" if left_is_better else "club_b"


def matchup_dimensions(
    club_a: MatchupClubSnapshot,
    club_b: MatchupClubSnapshot,
) -> list[MatchupDimensionData]:
    rows = [
        ("position", "最终排名", club_a.final_position, club_b.final_position, True, "最终积分榜名次"),
        ("points", "赛季积分", club_a.overall.points, club_b.overall.points, False, "38 场最终积分"),
        ("attack", "进攻产出", club_a.overall.goals_for, club_b.overall.goals_for, False, "赛季总进球"),
        ("defence", "防守失球", club_a.overall.goals_against, club_b.overall.goals_against, True, "失球更少占优"),
        ("home", "主场拿分", club_a.home.points, club_b.home.points, False, "19 个主场积分"),
        ("away", "客场拿分", club_a.away.points, club_b.away.points, False, "19 个客场积分"),
        ("recent", "末五场", club_a.recent_points, club_b.recent_points, False, "按真实开球日期计算"),
        ("unbeaten", "最长不败", club_a.longest_unbeaten, club_b.longest_unbeaten, False, "连续不败场次"),
    ]
    return [
        MatchupDimensionData(
            key=key,
            label=label,
            club_a_value=str(left),
            club_b_value=str(right),
            advantage=advantage(left, right, lower),
            note=note,
        )
        for key, label, left, right, lower, note in rows
    ]


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


@router.get("/matchup", response_model=ApiResponse[ClubMatchupData])
def get_club_matchup(
    club_a: str = Query(min_length=2),
    club_b: str = Query(min_length=2),
    season: str = Query(default=SAMPLE_SEASON, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
) -> ApiResponse[ClubMatchupData]:
    require_supported_season(season)
    if club_a == club_b:
        raise HTTPException(status_code=422, detail="请选择两支不同球队")

    clubs = list(db.scalars(select(Club).where(Club.slug.in_([club_a, club_b]))).all())
    clubs_by_slug = {club.slug: club for club in clubs}
    if club_a not in clubs_by_slug or club_b not in clubs_by_slug:
        raise HTTPException(status_code=404, detail="未找到对阵球队")

    standings = list(
        db.scalars(
            select(Standing).where(
                Standing.season == season,
                Standing.club_id.in_([clubs_by_slug[club_a].id, clubs_by_slug[club_b].id]),
            )
        ).all()
    )
    standings_by_club = {standing.club_id: standing for standing in standings}
    all_matches = list(db.scalars(season_result_query(season)).all())
    if len(standings) != 2 or len(all_matches) != 380:
        raise HTTPException(status_code=503, detail="赛季结果快照尚未完整初始化")

    first = clubs_by_slug[club_a]
    second = clubs_by_slug[club_b]
    first_matches = [match for match in all_matches if first.id in (match.home_club_id, match.away_club_id)]
    second_matches = [match for match in all_matches if second.id in (match.home_club_id, match.away_club_id)]
    direct_matches = chronological(
        match
        for match in all_matches
        if {match.home_club_id, match.away_club_id} == {first.id, second.id}
    )
    if len(first_matches) != 38 or len(second_matches) != 38 or len(direct_matches) != 2:
        raise HTTPException(status_code=503, detail="球队对阵数据尚未完整初始化")

    first_snapshot = matchup_snapshot(first, standings_by_club[first.id], first_matches)
    second_snapshot = matchup_snapshot(second, standings_by_club[second.id], second_matches)
    meetings: list[MatchupMeetingData] = []
    first_wins = second_wins = draws = first_goals = second_goals = 0
    for match in direct_matches:
        home_score = match.home_score or 0
        away_score = match.away_score or 0
        winner_slug = None
        if home_score > away_score:
            winner_slug = match.home_club.slug
        elif away_score > home_score:
            winner_slug = match.away_club.slug
        first_score = home_score if match.home_club_id == first.id else away_score
        second_score = home_score if match.home_club_id == second.id else away_score
        first_goals += first_score
        second_goals += second_score
        first_wins += winner_slug == first.slug
        second_wins += winner_slug == second.slug
        draws += winner_slug is None
        meetings.append(
            MatchupMeetingData(
                source_match_id=match.source_match_id or "",
                matchweek=match.matchweek,
                kickoff_at=match.kickoff_at,
                home_club=form_club(match.home_club),
                away_club=form_club(match.away_club),
                home_score=home_score,
                away_score=away_score,
                winner_slug=winner_slug,
            )
        )

    dimensions = matchup_dimensions(first_snapshot, second_snapshot)
    first_edges = sum(item.advantage == "club_a" for item in dimensions)
    second_edges = sum(item.advantage == "club_b" for item in dimensions)
    leader = first if first_edges > second_edges else second if second_edges > first_edges else None
    summary = [
        f"{first.name} 与 {second.name} 的比较只基于 2024-25 已完赛历史数据。",
        (
            f"{leader.name} 在 8 个确定性维度中占优更多，但这不是下一场比赛的胜率预测。"
            if leader
            else "两队在 8 个确定性维度中的优势数量相同，不据此推断未来胜负。"
        ),
        f"赛季两回合总比分为 {first.name} {first_goals}–{second_goals} {second.name}。",
    ]
    return ApiResponse(
        message="球队对阵简报获取成功",
        data=ClubMatchupData(
            competition=FORM_SNAPSHOT["competition"],
            season=season,
            snapshot_date=FORM_SNAPSHOT["snapshot_date"],
            club_a=first_snapshot,
            club_b=second_snapshot,
            head_to_head=MatchupHeadToHeadData(
                meetings=meetings,
                club_a_wins=first_wins,
                draws=draws,
                club_b_wins=second_wins,
                club_a_goals=first_goals,
                club_b_goals=second_goals,
            ),
            dimensions=dimensions,
            summary=summary,
            **source_fields(),
        ),
    )
