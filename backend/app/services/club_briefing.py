from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.database.seed import (
    SEASON_RESULTS_SOURCE_KIND,
    load_player_snapshot,
    load_season_results_snapshot,
)
from app.models import Club, Match, Standing
from app.schemas.briefing import (
    BriefingClubData,
    BriefingPosition,
    BriefingRecruitmentData,
    BriefingSeasonData,
    BriefingSourceData,
    ClubBriefingData,
)
from app.services.season_form import (
    build_record,
    longest_unbeaten_run,
    recent_form,
)
from app.services.squad_lens import get_squad_lens
from app.services.transfer_signal import get_transfer_signals


FORM_SNAPSHOT = load_season_results_snapshot()
PLAYER_SNAPSHOT = load_player_snapshot()
POSITION_LABELS: dict[BriefingPosition, str] = {
    "DEF": "后卫",
    "MID": "中场",
    "FWD": "前锋",
}
BRIEFING_LIMITATIONS = [
    "简报只组合项目内的固定历史快照，不联网补充实时排名、阵容、伤病或转会新闻。",
    "球员快照按球员—俱乐部记录保留转会分段；进球助攻汇总不等于球队赛果总进球。",
    "候选信号不包含身价、合同、工资、伤病、战术职责或实时可用性，不是签约建议。",
    "位置分钟只描述赛季记录结构，不能据此推断阵型、站位或未来比赛结果。",
]


class ClubBriefingUnavailable(RuntimeError):
    """Raised when one of the required fixed snapshots is incomplete."""


def _club_data(club: Club) -> BriefingClubData:
    return BriefingClubData(
        id=club.id,
        name=club.name,
        short_name=club.short_name,
        slug=club.slug,
        city=club.city,
        stadium_name=club.stadium_name,
        founded_year=club.founded_year,
        primary_color=club.primary_color,
    )


def _recent_points(results: list[str]) -> int:
    return sum(3 if result == "W" else 1 if result == "D" else 0 for result in results)


def get_club_briefing(
    db: Session,
    *,
    club_slug: str,
    season: str,
    minimum_minutes: int,
) -> ClubBriefingData | None:
    club = db.scalar(select(Club).where(Club.slug == club_slug))
    if club is None:
        return None

    standing = db.scalar(
        select(Standing).where(
            Standing.club_id == club.id,
            Standing.season == season,
        )
    )
    matches = list(
        db.scalars(
            select(Match)
            .options(
                selectinload(Match.home_club),
                selectinload(Match.away_club),
            )
            .where(
                Match.season == season,
                Match.source_kind == SEASON_RESULTS_SOURCE_KIND,
                or_(
                    Match.home_club_id == club.id,
                    Match.away_club_id == club.id,
                ),
            )
            .order_by(Match.kickoff_at, Match.matchweek, Match.id)
        ).all()
    )
    squad = get_squad_lens(
        db,
        club_slug=club.slug,
        season=season,
        minimum_minutes=minimum_minutes,
    )
    if standing is None or len(matches) != 38 or squad is None:
        raise ClubBriefingUnavailable("球队情报室所需的赛果或阵容快照尚未完整初始化")

    overall = build_record(matches, club.id)
    home = build_record(
        (match for match in matches if match.home_club_id == club.id),
        club.id,
    )
    away = build_record(
        (match for match in matches if match.away_club_id == club.id),
        club.id,
    )
    form = recent_form(matches, club.id)
    form_points = _recent_points(form)
    unbeaten = longest_unbeaten_run(matches, club.id)

    recruitment: list[BriefingRecruitmentData] = []
    for position in ("DEF", "MID", "FWD"):
        signals = get_transfer_signals(
            db,
            club_slug=club.slug,
            season=season,
            position=position,
            minimum_minutes=minimum_minutes,
            limit=1,
        )
        if signals is None or not signals.is_supported:
            raise ClubBriefingUnavailable("球队候选信号快照尚未完整初始化")
        candidate = signals.candidates[0] if signals.candidates else None
        need = signals.needs[0] if signals.needs else None
        if candidate is not None and need is not None:
            note = (
                f"首要观察 {need.label}（球队基线 P{need.club_percentile}）；"
                f"首位历史统计候选为 {candidate.full_name}，信号分 "
                f"{candidate.signal_score}/100。"
            )
        elif need is not None:
            note = (
                f"首要观察 {need.label}（球队基线 P{need.club_percentile}），"
                "但当前门槛没有产生正向候选信号。"
            )
        else:
            note = "当前门槛没有形成可解释的位置需求与候选信号。"
        recruitment.append(
            BriefingRecruitmentData(
                position=position,
                label=POSITION_LABELS[position],
                club_record_count=signals.club_record_count,
                peer_record_count=signals.peer_record_count,
                candidate_total=signals.candidate_total,
                needs=signals.needs,
                top_candidate=candidate,
                note=note,
            )
        )

    home_away_gap = round(home.points_per_game - away.points_per_game, 2)
    if abs(home_away_gap) <= 0.10:
        venue_headline = (
            f"主客场每场积分接近：主场 {home.points_per_game:.2f}，"
            f"客场 {away.points_per_game:.2f}。"
        )
    elif home_away_gap > 0:
        venue_headline = (
            f"主场每场积分比客场高 {home_away_gap:.2f}："
            f"{home.points_per_game:.2f} 对 {away.points_per_game:.2f}。"
        )
    else:
        venue_headline = (
            f"客场每场积分比主场高 {abs(home_away_gap):.2f}："
            f"{away.points_per_game:.2f} 对 {home.points_per_game:.2f}。"
        )

    goals_leader = next(
        leader for leader in squad.leaders if leader.metric == "goals"
    )
    recruitment_headline = "；".join(
        (
            f"{panel.label}优先看 {panel.needs[0].label} "
            f"P{panel.needs[0].club_percentile}"
        )
        for panel in recruitment
        if panel.needs
    )
    headlines = [
        (
            f"赛季终态：第 {standing.position} 名、{overall.points} 分，"
            f"净胜球 {overall.goal_difference:+d}。"
        ),
        venue_headline,
        (
            f"末五场为 {'-'.join(form)}，拿到 {form_points}/15 分；"
            f"赛季最长不败 {unbeaten} 场。"
        ),
        (
            f"{minimum_minutes}+ 分钟分析池包含 {squad.qualified_total}/"
            f"{squad.record_total} 条记录，前五出场记录占池内分钟 "
            f"{squad.top_five_minutes_share:.1f}%。"
        ),
        (
            f"队内进球领跑者为 {goals_leader.player.full_name}，"
            f"历史快照记录 {goals_leader.value} 球。"
        ),
        f"位置观察队列：{recruitment_headline}。",
    ]

    form_source = FORM_SNAPSHOT["source"]
    player_source = PLAYER_SNAPSHOT["source"]
    return ClubBriefingData(
        club=_club_data(club),
        competition=FORM_SNAPSHOT["competition"],
        season=season,
        snapshot_date=FORM_SNAPSHOT["snapshot_date"],
        minimum_minutes=minimum_minutes,
        season_summary=BriefingSeasonData(
            final_position=standing.position,
            overall=overall,
            home=home,
            away=away,
            recent_form=form,
            recent_points=form_points,
            longest_unbeaten=unbeaten,
        ),
        squad=squad,
        recruitment=recruitment,
        headlines=headlines,
        sources=[
            BriefingSourceData(
                name=form_source["name"],
                url=form_source["data_url"],
                license_name=form_source["license_name"],
                license_url=form_source["license_url"],
                scope="2024-25 完整 380 场赛果与球队赛季状态",
            ),
            BriefingSourceData(
                name=player_source["name"],
                url=player_source["dataset_url"],
                license_name=player_source["license_name"],
                license_url=player_source["license_url"],
                scope="2024-25 球员—俱乐部记录、阵容结构与候选信号",
            ),
        ],
        limitations=BRIEFING_LIMITATIONS,
        print_notice=(
            "使用浏览器打印功能可保存为 PDF；导出内容保留赛季、分钟门槛、"
            "数据来源与结论边界。"
        ),
    )
