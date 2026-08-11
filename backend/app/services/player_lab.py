from sqlalchemy.orm import Session

from app.database.seed import load_player_snapshot
from app.schemas.player import (
    PlayerClubData,
    PlayerLabData,
    PlayerLabItem,
    PlayerMetricPercentiles,
    PlayerPer90Metrics,
    PlayerPercentileProfile,
    PlayerPosition,
    PlayerSeasonTotals,
    PlayerSortKey,
    PlayerSortOrder,
)
from app.services.player_metrics import (
    PER90_METRIC_KEYS,
    PlayerSnapshot,
    load_player_snapshots,
    percentile_rank,
)

DEFAULT_MINIMUM_MINUTES = 450
MINIMUM_POSITION_PEERS = 3
PLAYER_SNAPSHOT = load_player_snapshot()
SAMPLE_NOTICE = (
    "当前球员中心使用 Kaggle v1 的 2024-25 历史快照：574 条球员—球队"
    "出场记录、562 个球员姓名与 20 支球队；12 条跨队附加记录按俱乐部"
    "分别保留。该快照不是实时名单。"
)
PERCENTILE_NOTICE = (
    "雷达图优先使用达到当前分钟门槛的同位置球员百分位；同位置不足"
    "3 条记录时回退到全部合格记录。切换到全部出场记录时，低分钟球员"
    "的每90数据可能波动较大。"
)


def _club_data(snapshot: PlayerSnapshot) -> PlayerClubData:
    club = snapshot.player.club
    return PlayerClubData(
        name=club.name,
        short_name=club.short_name,
        slug=club.slug,
        primary_color=club.primary_color,
    )


def _percentile_profile(
    snapshot: PlayerSnapshot,
    pool: list[PlayerSnapshot],
) -> PlayerPercentileProfile:
    position_peers = [
        item
        for item in pool
        if item.player.position == snapshot.player.position
    ]
    if len(position_peers) >= MINIMUM_POSITION_PEERS:
        peers = position_peers
        scope = "position_pool"
    else:
        peers = pool
        scope = "all_qualified_players"

    metrics = {
        key: percentile_rank(
            snapshot.per90[key],
            [item.per90[key] for item in peers],
        )
        for key in PER90_METRIC_KEYS
    }
    return PlayerPercentileProfile(
        scope=scope,
        peer_count=len(peers),
        metrics=PlayerMetricPercentiles(**metrics),
    )


def _to_item(
    snapshot: PlayerSnapshot,
    season: str,
    pool: list[PlayerSnapshot],
) -> PlayerLabItem:
    player = snapshot.player
    stats = snapshot.stats
    return PlayerLabItem(
        id=player.id,
        full_name=player.full_name,
        slug=player.slug,
        shirt_number=player.shirt_number,
        position=player.position,
        nationality=player.nationality,
        date_of_birth=player.date_of_birth,
        birth_year=player.birth_year,
        source_kind=player.source_kind,
        club=_club_data(snapshot),
        season=season,
        totals=PlayerSeasonTotals(
            appearances=stats.appearances,
            starts=stats.starts,
            minutes=stats.minutes,
            goals=stats.goals,
            assists=stats.assists,
            shots=stats.shots,
            key_passes=stats.key_passes,
            tackles=stats.tackles,
            interceptions=stats.interceptions,
            expected_goals=stats.expected_goals,
        ),
        per90=PlayerPer90Metrics(**snapshot.per90),
        percentiles=_percentile_profile(snapshot, pool),
    )


def _sort_value(item: PlayerLabItem, sort_by: PlayerSortKey) -> str | float:
    if sort_by == "full_name":
        return item.full_name.casefold()
    if sort_by == "club":
        return item.club.short_name.casefold()
    if sort_by == "position":
        return item.position
    if sort_by in {
        "goals_per90",
        "assists_per90",
        "shots_per90",
        "key_passes_per90",
        "tackles_per90",
        "interceptions_per90",
        "expected_goals_per90",
    }:
        return getattr(item.per90, sort_by)
    return float(getattr(item.totals, sort_by))


def list_player_lab(
    db: Session,
    *,
    season: str,
    minimum_minutes: int,
    query: str | None,
    position: PlayerPosition | None,
    club_slug: str | None,
    sort_by: PlayerSortKey,
    order: PlayerSortOrder,
    limit: int,
    offset: int,
) -> PlayerLabData:
    dataset = load_player_snapshots(db, season, 0)
    pool = [
        snapshot
        for snapshot in dataset
        if snapshot.stats.minutes >= minimum_minutes
    ]
    items = [_to_item(snapshot, season, pool) for snapshot in pool]

    normalized_query = query.strip().casefold() if query else ""
    if normalized_query:
        items = [
            item
            for item in items
            if any(
                normalized_query in value.casefold()
                for value in (
                    item.full_name,
                    item.club.name,
                    item.club.short_name,
                    item.nationality,
                )
            )
        ]
    if position:
        items = [item for item in items if item.position == position]
    if club_slug:
        items = [item for item in items if item.club.slug == club_slug]

    reverse = order == "desc"
    items.sort(
        key=lambda item: (_sort_value(item, sort_by), item.full_name),
        reverse=reverse,
    )
    total = len(items)
    page_items = items[offset : offset + limit]

    clubs_by_slug = {
        snapshot.player.club.slug: _club_data(snapshot)
        for snapshot in dataset
    }
    available_positions = sorted(
        {snapshot.player.position for snapshot in dataset},
        key=("GK", "DEF", "MID", "FWD").index,
    )

    return PlayerLabData(
        items=page_items,
        total=total,
        pool_total=len(pool),
        dataset_total=len(dataset),
        unique_player_total=len(
            {snapshot.player.full_name for snapshot in dataset}
        ),
        transfer_record_total=len(dataset)
        - len({snapshot.player.full_name for snapshot in dataset}),
        season=season,
        minimum_minutes=minimum_minutes,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        available_positions=available_positions,
        available_clubs=sorted(
            clubs_by_slug.values(),
            key=lambda club: club.short_name,
        ),
        source_name=PLAYER_SNAPSHOT["source"]["name"],
        source_url=PLAYER_SNAPSHOT["source"]["dataset_url"],
        source_version=PLAYER_SNAPSHOT["source"]["dataset_version"],
        license_name=PLAYER_SNAPSHOT["source"]["license_name"],
        license_url=PLAYER_SNAPSHOT["source"]["license_url"],
        sample_notice=SAMPLE_NOTICE,
        percentile_notice=PERCENTILE_NOTICE,
    )


def get_player_lab_item(
    db: Session,
    *,
    slug: str,
    season: str,
) -> PlayerLabItem | None:
    snapshots = load_player_snapshots(db, season)
    snapshot = next(
        (item for item in snapshots if item.player.slug == slug),
        None,
    )
    if snapshot is None:
        return None

    percentile_pool = load_player_snapshots(
        db,
        season,
        DEFAULT_MINIMUM_MINUTES,
    )
    return _to_item(snapshot, season, percentile_pool)
