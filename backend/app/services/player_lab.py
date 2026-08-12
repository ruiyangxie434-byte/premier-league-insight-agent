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
    PlayerSimilarityCandidate,
    PlayerSimilarityData,
    PlayerSimilarityDifference,
    PlayerSimilarityMetricWeight,
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

SIMILARITY_METRIC_LABELS = {
    "goals_per90": "进球",
    "assists_per90": "助攻",
    "shots_per90": "射门",
    "key_passes_per90": "关键传球",
    "tackles_per90": "抢断",
    "interceptions_per90": "拦截",
    "expected_goals_per90": "预期进球",
}
SIMILARITY_WEIGHTS: dict[PlayerPosition, dict[str, float]] = {
    "FWD": {
        "goals_per90": 0.25,
        "assists_per90": 0.15,
        "shots_per90": 0.18,
        "key_passes_per90": 0.16,
        "tackles_per90": 0.08,
        "interceptions_per90": 0.06,
        "expected_goals_per90": 0.12,
    },
    "MID": {
        "goals_per90": 0.10,
        "assists_per90": 0.16,
        "shots_per90": 0.10,
        "key_passes_per90": 0.22,
        "tackles_per90": 0.16,
        "interceptions_per90": 0.14,
        "expected_goals_per90": 0.12,
    },
    "DEF": {
        "goals_per90": 0.05,
        "assists_per90": 0.08,
        "shots_per90": 0.05,
        "key_passes_per90": 0.12,
        "tackles_per90": 0.25,
        "interceptions_per90": 0.30,
        "expected_goals_per90": 0.05,
    },
}
SIMILARITY_METHOD_NOTICE = (
    "相似度只比较达到分钟门槛的同位置记录。系统先把七项每90指标转换为"
    "同位置百分位，再按位置权重计算绝对差异；100 表示当前指标画像完全"
    "一致。结果排除目标球员本人及其其他俱乐部分段，不代表转会建议或"
    "绝对能力排名。"
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


def find_similar_players(
    db: Session,
    *,
    slug: str,
    season: str,
    minimum_minutes: int,
    limit: int,
) -> PlayerSimilarityData | None:
    dataset = load_player_snapshots(db, season, 0)
    target_snapshot = next(
        (item for item in dataset if item.player.slug == slug),
        None,
    )
    if target_snapshot is None:
        return None

    qualified_pool = [
        item
        for item in dataset
        if item.stats.minutes >= minimum_minutes
    ]
    target = _to_item(target_snapshot, season, qualified_pool)
    candidate_pool = [
        item
        for item in qualified_pool
        if item.player.position == target_snapshot.player.position
        and item.player.full_name != target_snapshot.player.full_name
    ]
    position_pool = [
        item
        for item in qualified_pool
        if item.player.position == target_snapshot.player.position
    ]

    unsupported_reason: str | None = None
    if target_snapshot.player.position == "GK":
        unsupported_reason = (
            "当前快照缺少扑救、失球和零封等门将指标，暂不生成可能误导的"
            "门将相似度。"
        )
    elif target_snapshot.stats.minutes <= 0:
        unsupported_reason = "该球员记录没有有效比赛分钟，无法计算可靠的每90画像。"
    elif len(position_pool) < MINIMUM_POSITION_PEERS or not candidate_pool:
        unsupported_reason = (
            "当前分钟门槛下的同位置合格记录不足 3 条，无法建立稳定的"
            "百分位比较池。"
        )

    weights = SIMILARITY_WEIGHTS.get(target_snapshot.player.position, {})
    metric_weights = [
        PlayerSimilarityMetricWeight(
            key=key,
            label=SIMILARITY_METRIC_LABELS[key],
            weight=weight,
        )
        for key, weight in weights.items()
    ]
    if unsupported_reason is not None:
        return PlayerSimilarityData(
            target=target,
            items=[],
            candidate_total=len(candidate_pool),
            season=season,
            minimum_minutes=minimum_minutes,
            position=target_snapshot.player.position,
            is_supported=False,
            unavailable_reason=unsupported_reason,
            metric_weights=metric_weights,
            method_notice=SIMILARITY_METHOD_NOTICE,
            sample_notice=SAMPLE_NOTICE,
        )

    target_percentiles = target.percentiles.metrics.model_dump()
    ranked: list[tuple[float, PlayerSimilarityCandidate]] = []
    for candidate_snapshot in candidate_pool:
        candidate = _to_item(candidate_snapshot, season, qualified_pool)
        candidate_percentiles = candidate.percentiles.metrics.model_dump()
        gaps = {
            key: abs(target_percentiles[key] - candidate_percentiles[key])
            for key in weights
        }
        distance = sum(weights[key] * gaps[key] for key in weights)
        closest_keys = sorted(
            weights,
            key=lambda key: (gaps[key], -weights[key], key),
        )[:2]
        contrast_key = max(
            weights,
            key=lambda key: (weights[key] * gaps[key], gaps[key], key),
        )
        ranked.append(
            (
                distance,
                PlayerSimilarityCandidate(
                    player=candidate,
                    similarity_score=max(0, min(100, round(100 - distance))),
                    closest_metrics=[
                        SIMILARITY_METRIC_LABELS[key]
                        for key in closest_keys
                    ],
                    key_difference=PlayerSimilarityDifference(
                        key=contrast_key,
                        label=SIMILARITY_METRIC_LABELS[contrast_key],
                        target_percentile=target_percentiles[contrast_key],
                        candidate_percentile=candidate_percentiles[contrast_key],
                        gap=gaps[contrast_key],
                    ),
                ),
            )
        )

    ranked.sort(
        key=lambda item: (
            item[0],
            -item[1].player.totals.minutes,
            item[1].player.full_name.casefold(),
            item[1].player.slug,
        )
    )
    return PlayerSimilarityData(
        target=target,
        items=[item for _, item in ranked[:limit]],
        candidate_total=len(candidate_pool),
        season=season,
        minimum_minutes=minimum_minutes,
        position=target_snapshot.player.position,
        is_supported=True,
        unavailable_reason=None,
        metric_weights=metric_weights,
        method_notice=SIMILARITY_METHOD_NOTICE,
        sample_notice=SAMPLE_NOTICE,
    )
