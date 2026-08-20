from __future__ import annotations

from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.seed import load_player_snapshot
from app.models import Club
from app.schemas.transfer import (
    TransferCandidateData,
    TransferClubData,
    TransferMetricGap,
    TransferMetricKey,
    TransferNeedMetric,
    TransferPosition,
    TransferSignalData,
)
from app.services.player_lab import (
    SIMILARITY_METRIC_LABELS,
    SIMILARITY_WEIGHTS,
)
from app.services.player_metrics import (
    PlayerSnapshot,
    load_player_snapshots,
    percentile_rank,
)


PLAYER_SNAPSHOT = load_player_snapshot()
SAMPLE_NOTICE = (
    "候选信号来自 Kaggle v1 的 2024-25 历史球员—球队快照；转会分段"
    "按俱乐部记录保留，页面不是当前名单、新闻或实时转会数据库。"
)
METHOD_NOTICE = (
    "系统先在同位置、达到分钟门槛的记录中计算七项每90百分位，再用目标"
    "球队该位置记录的平均百分位建立基线。优先级来自位置权重与基线缺口；"
    "候选分综合正向百分位提升、位置画像和样本分钟，只用于排序统计信号。"
)
DECISION_NOTICE = (
    "信号分不是成交概率、能力总评或转会建议。数据不包含身价、合同、工资、"
    "伤病、可用性、战术职责、门将专属指标和未来表现，实际决策必须补充这些变量。"
)


def _club_data(club: Club) -> TransferClubData:
    return TransferClubData(
        name=club.name,
        short_name=club.short_name,
        slug=club.slug,
        primary_color=club.primary_color,
    )


def _metric_percentiles(
    snapshot: PlayerSnapshot,
    peers: list[PlayerSnapshot],
    keys: tuple[TransferMetricKey, ...],
) -> dict[TransferMetricKey, int]:
    return {
        key: percentile_rank(
            snapshot.per90[key],
            [item.per90[key] for item in peers],
        )
        for key in keys
    }


def _gap_data(
    key: TransferMetricKey,
    club_percentile: int,
    candidate_percentile: int,
) -> TransferMetricGap:
    return TransferMetricGap(
        key=key,
        label=SIMILARITY_METRIC_LABELS[key],
        club_percentile=club_percentile,
        candidate_percentile=candidate_percentile,
        gap=candidate_percentile - club_percentile,
    )


def get_transfer_signals(
    db: Session,
    *,
    club_slug: str,
    season: str,
    position: TransferPosition,
    minimum_minutes: int,
    limit: int,
) -> TransferSignalData | None:
    club = db.scalar(select(Club).where(Club.slug == club_slug))
    if club is None:
        return None

    dataset = load_player_snapshots(db, season, 0)
    position_pool = [
        item
        for item in dataset
        if item.player.position == position
        and item.stats.minutes >= minimum_minutes
    ]
    club_records = [
        item for item in position_pool if item.player.club_id == club.id
    ]
    base_result = {
        "club": _club_data(club),
        "season": season,
        "position": position,
        "minimum_minutes": minimum_minutes,
        "limit": limit,
        "club_record_count": len(club_records),
        "peer_record_count": len(position_pool),
        "source_name": PLAYER_SNAPSHOT["source"]["name"],
        "source_url": PLAYER_SNAPSHOT["source"]["dataset_url"],
        "source_version": PLAYER_SNAPSHOT["source"]["dataset_version"],
        "license_name": PLAYER_SNAPSHOT["source"]["license_name"],
        "license_url": PLAYER_SNAPSHOT["source"]["license_url"],
        "sample_notice": SAMPLE_NOTICE,
        "method_notice": METHOD_NOTICE,
        "decision_notice": DECISION_NOTICE,
    }

    if position == "GK":
        return TransferSignalData(
            **base_result,
            is_supported=False,
            unavailable_reason=(
                "当前快照缺少扑救、失球、阻止进球和传中处理等门将专属指标，"
                "因此不生成可能误导的门将候选信号。"
            ),
            candidate_total=0,
            needs=[],
            candidates=[],
        )
    if not club_records:
        return TransferSignalData(
            **base_result,
            is_supported=False,
            unavailable_reason="目标球队在当前位置与分钟门槛下没有可用基线记录。",
            candidate_total=0,
            needs=[],
            candidates=[],
        )

    weights = SIMILARITY_WEIGHTS[position]
    metric_keys = tuple(weights)
    percentile_rows = {
        item.player.id: _metric_percentiles(item, position_pool, metric_keys)
        for item in position_pool
    }
    club_profile = {
        key: round(
            mean(percentile_rows[item.player.id][key] for item in club_records)
        )
        for key in metric_keys
    }

    raw_priorities = {
        key: weights[key] * (100 - club_profile[key])
        for key in metric_keys
    }
    need_keys = sorted(
        metric_keys,
        key=lambda key: (
            -raw_priorities[key],
            club_profile[key],
            key,
        ),
    )[:3]
    priority_total = sum(raw_priorities[key] for key in need_keys) or 1.0
    normalized_priorities = {
        key: raw_priorities[key] / priority_total for key in need_keys
    }
    needs = [
        TransferNeedMetric(
            key=key,
            label=SIMILARITY_METRIC_LABELS[key],
            club_percentile=club_profile[key],
            priority=round(normalized_priorities[key] * 100),
        )
        for key in need_keys
    ]

    target_player_names = {
        item.player.full_name for item in club_records
    }
    external_records = [
        item
        for item in position_pool
        if item.player.club_id != club.id
        and item.player.full_name not in target_player_names
    ]
    ranked: list[tuple[int, int, str, TransferCandidateData]] = []
    for item in external_records:
        candidate_profile = percentile_rows[item.player.id]
        positive_lifts = [
            _gap_data(key, club_profile[key], candidate_profile[key])
            for key in need_keys
            if candidate_profile[key] > club_profile[key]
        ]
        if not positive_lifts:
            continue

        lift_score = sum(
            max(0, candidate_profile[key] - club_profile[key])
            * normalized_priorities[key]
            for key in need_keys
        )
        profile_score = sum(
            candidate_profile[key] * weights[key] for key in metric_keys
        )
        confidence_score = min(100, round(item.stats.minutes / 2700 * 100))
        signal_score = max(
            0,
            min(
                100,
                round(
                    lift_score * 0.60
                    + profile_score * 0.30
                    + confidence_score * 0.10
                ),
            ),
        )
        tradeoffs = [
            _gap_data(key, club_profile[key], candidate_profile[key])
            for key in metric_keys
            if candidate_profile[key] < club_profile[key]
        ]
        tradeoffs.sort(key=lambda gap: (gap.gap, gap.key))
        positive_lifts.sort(key=lambda gap: (-gap.gap, gap.key))
        candidate = TransferCandidateData(
            full_name=item.player.full_name,
            slug=item.player.slug,
            position=position,
            nationality=item.player.nationality,
            birth_year=item.player.birth_year,
            club=_club_data(item.player.club),
            appearances=item.stats.appearances,
            minutes=item.stats.minutes,
            signal_score=signal_score,
            confidence_score=confidence_score,
            key_lifts=positive_lifts[:3],
            tradeoffs=tradeoffs[:2],
        )
        ranked.append(
            (
                -signal_score,
                -item.stats.minutes,
                item.player.full_name.casefold(),
                candidate,
            )
        )

    ranked.sort(key=lambda item: item[:3])
    unique_candidates: list[TransferCandidateData] = []
    seen_names: set[str] = set()
    for _, _, _, candidate in ranked:
        if candidate.full_name in seen_names:
            continue
        unique_candidates.append(candidate)
        seen_names.add(candidate.full_name)

    return TransferSignalData(
        **base_result,
        is_supported=True,
        unavailable_reason=None,
        candidate_total=len(unique_candidates),
        needs=needs,
        candidates=unique_candidates[:limit],
    )
