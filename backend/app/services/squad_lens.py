from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.seed import load_player_snapshot
from app.models import Club
from app.schemas.squad import (
    SquadClubData,
    SquadLeaderData,
    SquadLensData,
    SquadPlayerData,
    SquadPosition,
    SquadPositionGroup,
)
from app.services.player_metrics import PlayerSnapshot, load_player_snapshots


POSITION_LABELS: dict[SquadPosition, str] = {
    "GK": "门将",
    "DEF": "后卫",
    "MID": "中场",
    "FWD": "前锋",
}
POSITION_ORDER: tuple[SquadPosition, ...] = ("GK", "DEF", "MID", "FWD")
PLAYER_SNAPSHOT = load_player_snapshot()
SAMPLE_NOTICE = (
    "阵容数据来自 Kaggle v1 的 2024-25 历史球员—球队快照，转会分段按"
    "俱乐部分别保留；页面展示的是赛季记录，不是当前实时名单。"
)
METHOD_NOTICE = (
    "所有汇总只计算达到所选分钟门槛的记录。位置占比和前五负荷均以这些"
    "记录的球员出场分钟总和为分母；进球与助攻之和不等于球队赛季总进球，"
    "也不用于预测未来表现。"
)


def _share(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(value / total * 100, 1)


def _player_data(snapshot: PlayerSnapshot, total_minutes: int) -> SquadPlayerData:
    player = snapshot.player
    stats = snapshot.stats
    return SquadPlayerData(
        full_name=player.full_name,
        slug=player.slug,
        position=player.position,
        nationality=player.nationality,
        appearances=stats.appearances,
        starts=stats.starts,
        minutes=stats.minutes,
        goals=stats.goals,
        assists=stats.assists,
        minutes_share=_share(stats.minutes, total_minutes),
    )


def _leader(
    snapshots: list[PlayerSnapshot],
    *,
    metric: str,
    label: str,
    unit: str,
    total_minutes: int,
) -> SquadLeaderData:
    def metric_value(snapshot: PlayerSnapshot) -> int:
        if metric == "defensive_actions":
            return snapshot.stats.tackles + snapshot.stats.interceptions
        return int(getattr(snapshot.stats, metric))

    leader = max(
        snapshots,
        key=lambda item: (
            metric_value(item),
            item.stats.minutes,
            item.player.full_name,
        ),
    )
    return SquadLeaderData(
        metric=metric,
        label=label,
        value=metric_value(leader),
        unit=unit,
        player=_player_data(leader, total_minutes),
    )


def get_squad_lens(
    db: Session,
    *,
    club_slug: str,
    season: str,
    minimum_minutes: int,
) -> SquadLensData | None:
    club = db.scalar(select(Club).where(Club.slug == club_slug))
    if club is None:
        return None

    records = [
        item
        for item in load_player_snapshots(db, season, 0)
        if item.player.club_id == club.id
    ]
    qualified = [
        item for item in records if item.stats.minutes >= minimum_minutes
    ]
    if not qualified:
        return None

    total_minutes = sum(item.stats.minutes for item in qualified)
    total_goals = sum(item.stats.goals for item in qualified)
    total_assists = sum(item.stats.assists for item in qualified)

    position_groups: list[SquadPositionGroup] = []
    for position in POSITION_ORDER:
        items = [item for item in qualified if item.player.position == position]
        minutes = sum(item.stats.minutes for item in items)
        goals = sum(item.stats.goals for item in items)
        assists = sum(item.stats.assists for item in items)
        position_groups.append(
            SquadPositionGroup(
                position=position,
                label=POSITION_LABELS[position],
                record_count=len(items),
                minutes=minutes,
                minutes_share=_share(minutes, total_minutes),
                goals=goals,
                assists=assists,
                goal_contributions=goals + assists,
            )
        )

    by_minutes = sorted(
        qualified,
        key=lambda item: (-item.stats.minutes, item.player.full_name),
    )
    core_players = [
        _player_data(item, total_minutes) for item in by_minutes[:8]
    ]
    top_five_minutes = sum(item.stats.minutes for item in by_minutes[:5])
    dominant_position = max(
        position_groups,
        key=lambda item: (item.minutes, -POSITION_ORDER.index(item.position)),
    )
    attack_position = max(
        position_groups,
        key=lambda item: (
            item.goal_contributions,
            item.goals,
            -POSITION_ORDER.index(item.position),
        ),
    )

    leaders = [
        _leader(
            qualified,
            metric="minutes",
            label="出场时间",
            unit="分钟",
            total_minutes=total_minutes,
        ),
        _leader(
            qualified,
            metric="goals",
            label="进球",
            unit="球",
            total_minutes=total_minutes,
        ),
        _leader(
            qualified,
            metric="assists",
            label="助攻",
            unit="次",
            total_minutes=total_minutes,
        ),
        _leader(
            qualified,
            metric="key_passes",
            label="关键传球",
            unit="次",
            total_minutes=total_minutes,
        ),
        _leader(
            qualified,
            metric="defensive_actions",
            label="抢断 + 拦截",
            unit="次",
            total_minutes=total_minutes,
        ),
    ]

    return SquadLensData(
        club=SquadClubData(
            id=club.id,
            name=club.name,
            short_name=club.short_name,
            slug=club.slug,
            primary_color=club.primary_color,
        ),
        season=season,
        minimum_minutes=minimum_minutes,
        record_total=len(records),
        qualified_total=len(qualified),
        excluded_total=len(records) - len(qualified),
        total_minutes=total_minutes,
        total_goals=total_goals,
        total_assists=total_assists,
        unique_nationalities=len(
            {item.player.nationality for item in qualified}
        ),
        top_five_minutes_share=_share(top_five_minutes, total_minutes),
        position_groups=position_groups,
        leaders=leaders,
        core_players=core_players,
        summary=[
            (
                f"{dominant_position.label}贡献 "
                f"{dominant_position.minutes_share:.1f}% 的分析池出场分钟。"
            ),
            (
                f"{attack_position.label}合计贡献 "
                f"{attack_position.goal_contributions} 次进球或助攻。"
            ),
            (
                "队内出场前五名合计占分析池分钟的 "
                f"{_share(top_five_minutes, total_minutes):.1f}%。"
            ),
        ],
        source_name=PLAYER_SNAPSHOT["source"]["name"],
        source_url=PLAYER_SNAPSHOT["source"]["dataset_url"],
        source_version=PLAYER_SNAPSHOT["source"]["dataset_version"],
        license_name=PLAYER_SNAPSHOT["source"]["license_name"],
        license_url=PLAYER_SNAPSHOT["source"]["license_url"],
        sample_notice=SAMPLE_NOTICE,
        method_notice=METHOD_NOTICE,
    )
