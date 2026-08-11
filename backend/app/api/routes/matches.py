from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database.seed import load_match_snapshot
from app.database.session import get_db
from app.models import Club, Match, MatchEvent
from app.schemas.common import ApiResponse
from app.schemas.match import (
    MatchDetailData,
    MatchListData,
    MatchShotData,
    MatchSummaryData,
    MatchTeamData,
)

router = APIRouter(prefix="/matches", tags=["matches"])

MATCH_SNAPSHOT = load_match_snapshot()
MATCH_SOURCE = MATCH_SNAPSHOT["source"]
MATCH_SOURCE_KIND = "open-data"
MATCH_COMPETITION = MATCH_SNAPSHOT["match"]["competition"]
MATCH_SAMPLE_NOTICE = (
    "当前仅提供一场 2003-04 历史英超公开事件快照；"
    "它与 2024-25 球员赛季快照属于不同赛季，不用于实时结论。"
)
COORDINATE_NOTE = (
    "射门坐标由 StatsBomb 120×80 坐标系归一化为 0-100；"
    "所有射门按进攻方向展示，位置点不代表球员跑动轨迹。"
)
INTERPRETATION_NOTE = (
    "xG 用于描述射门机会质量，不等同于必然进球；"
    "本页只分析射门事件，不推断控球率、阵型或无球跑动。"
)


def match_query():
    return select(Match).options(
        selectinload(Match.home_club),
        selectinload(Match.away_club),
        selectinload(Match.events).selectinload(MatchEvent.club),
    )


def shot_events(match: Match) -> list[MatchEvent]:
    return sorted(
        (event for event in match.events if event.event_type == "shot"),
        key=lambda event: (event.minute, event.second, event.id),
    )


def team_data(
    club: Club,
    score: int | None,
    events: list[MatchEvent],
) -> MatchTeamData:
    team_shots = [event for event in events if event.club_id == club.id]
    return MatchTeamData(
        id=club.id,
        name=club.name,
        short_name=club.short_name,
        slug=club.slug,
        primary_color=club.primary_color,
        score=score or 0,
        shots=len(team_shots),
        goals=sum(event.outcome == "Goal" for event in team_shots),
        total_xg=round(sum(event.xg or 0 for event in team_shots), 3),
    )


def match_summary(match: Match) -> MatchSummaryData:
    events = shot_events(match)
    home_team = team_data(match.home_club, match.home_score, events)
    away_team = team_data(match.away_club, match.away_score, events)
    if match.source_match_id is None:
        raise ValueError("Public match is missing its source identifier")
    return MatchSummaryData(
        source_match_id=match.source_match_id,
        competition=MATCH_COMPETITION,
        season=match.season,
        matchweek=match.matchweek,
        kickoff_at=match.kickoff_at,
        venue=match.venue,
        status=match.status,
        home_team=home_team,
        away_team=away_team,
        shot_count=len(events),
        goal_count=(match.home_score or 0) + (match.away_score or 0),
        total_xg=round(home_team.total_xg + away_team.total_xg, 3),
        source_kind=match.source_kind,
    )


@router.get("", response_model=ApiResponse[MatchListData])
def list_matches(db: Session = Depends(get_db)) -> ApiResponse[MatchListData]:
    matches = db.scalars(
        match_query()
        .where(Match.source_kind == MATCH_SOURCE_KIND)
        .order_by(Match.kickoff_at.desc())
    ).all()
    total = db.scalar(
        select(func.count(Match.id)).where(
            Match.source_kind == MATCH_SOURCE_KIND
        )
    ) or 0
    return ApiResponse(
        message="比赛快照获取成功",
        data=MatchListData(
            items=[match_summary(match) for match in matches],
            total=total,
            source_name=MATCH_SOURCE["name"],
            source_url=MATCH_SOURCE["repository_url"],
            license_url=MATCH_SOURCE["license_url"],
            sample_notice=MATCH_SAMPLE_NOTICE,
        ),
    )


@router.get("/{source_match_id}", response_model=ApiResponse[MatchDetailData])
def get_match(
    source_match_id: str,
    db: Session = Depends(get_db),
) -> ApiResponse[MatchDetailData]:
    match = db.scalar(
        match_query().where(Match.source_match_id == source_match_id)
    )
    if match is None:
        raise HTTPException(status_code=404, detail="未找到该比赛快照")

    summary = match_summary(match)
    colors = {
        match.home_club_id: match.home_club.primary_color,
        match.away_club_id: match.away_club.primary_color,
    }
    slugs = {
        match.home_club_id: match.home_club.slug,
        match.away_club_id: match.away_club.slug,
    }
    shots = [
        MatchShotData(
            source_event_id=event.source_event_id or str(event.id),
            period=event.period,
            minute=event.minute,
            second=event.second,
            team_name=event.club.name,
            team_slug=slugs[event.club_id],
            team_color=colors[event.club_id],
            player_name=event.player_name,
            outcome=event.outcome or "Unknown",
            is_goal=event.outcome == "Goal",
            x=event.x or 0,
            y=event.y or 0,
            xg=round(event.xg or 0, 3),
            body_part=event.body_part,
            shot_type=event.shot_type,
            play_pattern=event.play_pattern,
        )
        for event in shot_events(match)
    ]

    return ApiResponse(
        message="比赛详情获取成功",
        data=MatchDetailData(
            **summary.model_dump(),
            shots=shots,
            source_name=MATCH_SOURCE["name"],
            source_url=MATCH_SOURCE["events_url"],
            license_url=MATCH_SOURCE["license_url"],
            source_last_updated=MATCH_SOURCE["source_last_updated"],
            coordinate_note=COORDINATE_NOTE,
            interpretation_note=INTERPRETATION_NOTE,
        ),
    )
