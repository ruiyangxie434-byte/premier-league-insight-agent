from collections import defaultdict
from uuid import uuid4

from sqlalchemy.orm import Session

from app.schemas.agent import (
    AgentAnalysisData,
    AgentAnalysisRequest,
    AgentEvidence,
    AgentFocus,
    AgentGeneration,
    AgentMetricComparison,
    AgentMetricValue,
    AgentPlayerOption,
    AgentPlayerOptionData,
    AgentPlayerProfile,
    AgentRecommendation,
    AgentStep,
)
from app.services.player_metrics import (
    PlayerSnapshot,
    load_player_snapshots,
    percentile_rank,
)
from app.services.player_lab import DEFAULT_MINIMUM_MINUTES

SAMPLE_NOTICE = (
    "当前结论使用 2024-25 历史快照中达到 450 分钟的 400 条球员—球队"
    "记录；百分位按该固定分析池计算，不代表实时球探意见。"
)

FOCUS_LABELS: dict[AgentFocus, str] = {
    "balanced": "综合表现",
    "scoring": "终结与得分",
    "creativity": "创造与组织",
    "pressing": "高位逼抢适配",
}

METRICS = {
    "goals_per90": ("进球", "每90分钟"),
    "assists_per90": ("助攻", "每90分钟"),
    "shots_per90": ("射门", "每90分钟"),
    "key_passes_per90": ("关键传球", "每90分钟"),
    "tackles_per90": ("抢断", "每90分钟"),
    "interceptions_per90": ("拦截", "每90分钟"),
    "expected_goals_per90": ("预期进球", "每90分钟"),
}

FOCUS_WEIGHTS: dict[AgentFocus, dict[str, float]] = {
    "balanced": {
        "goals_per90": 0.22,
        "assists_per90": 0.17,
        "shots_per90": 0.10,
        "key_passes_per90": 0.18,
        "tackles_per90": 0.17,
        "interceptions_per90": 0.16,
    },
    "scoring": {
        "goals_per90": 0.34,
        "expected_goals_per90": 0.27,
        "shots_per90": 0.20,
        "assists_per90": 0.10,
        "key_passes_per90": 0.09,
    },
    "creativity": {
        "key_passes_per90": 0.34,
        "assists_per90": 0.30,
        "shots_per90": 0.10,
        "goals_per90": 0.12,
        "tackles_per90": 0.07,
        "interceptions_per90": 0.07,
    },
    "pressing": {
        "tackles_per90": 0.34,
        "interceptions_per90": 0.28,
        "key_passes_per90": 0.13,
        "assists_per90": 0.09,
        "goals_per90": 0.09,
        "shots_per90": 0.07,
    },
}

PLAYER_ALIASES = {
    "萨卡": "bukayo-saka",
    "帕尔默": "cole-palmer",
    "萨拉赫": "mohamed-salah",
    "哈兰德": "erling-haaland",
    "伊萨克": "alexander-isak",
    "福登": "phil-foden",
    "赖斯": "declan-rice",
    "沃特金斯": "ollie-watkins",
    "范戴克": "virgil-van-dijk",
    "凯塞多": "moises-caicedo",
}

FOCUS_KEYWORDS: dict[AgentFocus, tuple[str, ...]] = {
    "scoring": (
        "进球",
        "得分",
        "终结",
        "射门",
        "xg",
        "破门",
    ),
    "creativity": (
        "创造",
        "组织",
        "助攻",
        "关键传球",
        "传球",
        "机会",
    ),
    "pressing": (
        "逼抢",
        "压迫",
        "抢断",
        "拦截",
        "防守",
        "反抢",
    ),
    "balanced": (
        "综合",
        "全面",
        "整体",
        "攻防",
    ),
}


class AgentInputError(ValueError):
    pass


def _resolve_focus(request: AgentAnalysisRequest) -> AgentFocus:
    if request.focus != "auto":
        return request.focus

    question = request.question.casefold()
    keyword_scores = {
        focus: sum(keyword in question for keyword in keywords)
        for focus, keywords in FOCUS_KEYWORDS.items()
    }
    best_focus = max(keyword_scores, key=keyword_scores.get)
    if keyword_scores[best_focus] == 0:
        return "balanced"
    return best_focus


def list_agent_players(db: Session, season: str) -> AgentPlayerOptionData:
    snapshots = load_player_snapshots(db, season, DEFAULT_MINIMUM_MINUTES)
    return AgentPlayerOptionData(
        items=[
            AgentPlayerOption(
                slug=item.player.slug,
                full_name=item.player.full_name,
                club_name=item.player.club.short_name,
                club_color=item.player.club.primary_color,
                position=item.player.position,
                minutes=item.stats.minutes,
            )
            for item in snapshots
        ],
        total=len(snapshots),
        season=season,
        sample_notice=SAMPLE_NOTICE,
    )


def _resolve_player_slugs(
    request: AgentAnalysisRequest,
    snapshots: list[PlayerSnapshot],
) -> list[str]:
    available = {item.player.slug: item for item in snapshots}
    if request.player_slugs is not None:
        missing = [slug for slug in request.player_slugs if slug not in available]
        if missing:
            raise AgentInputError(f"没有找到球员：{', '.join(missing)}")
        return request.player_slugs

    question = request.question.casefold()
    matched: list[str] = []
    by_name: defaultdict[str, list[PlayerSnapshot]] = defaultdict(list)
    for snapshot in snapshots:
        by_name[snapshot.player.full_name.casefold()].append(snapshot)

    for full_name, name_records in by_name.items():
        slug_mentions = [
            item
            for item in name_records
            if item.player.slug.replace("-", " ").casefold() in question
        ]
        if slug_mentions:
            matched.extend(item.player.slug for item in slug_mentions)
            continue
        if full_name not in question:
            continue
        if len(name_records) == 1:
            matched.append(name_records[0].player.slug)
            continue
        for item in name_records:
            club = item.player.club
            if any(
                candidate.casefold() in question
                for candidate in (
                    club.name,
                    club.short_name,
                    club.slug.replace("-", " "),
                )
            ):
                matched.append(item.player.slug)

    last_names: defaultdict[str, list[PlayerSnapshot]] = defaultdict(list)
    for snapshot in snapshots:
        last_names[snapshot.player.full_name.split()[-1].casefold()].append(
            snapshot
        )
    for last_name, name_records in last_names.items():
        if (
            len(name_records) == 1
            and last_name in question
            and name_records[0].player.slug not in matched
        ):
            matched.append(name_records[0].player.slug)

    for alias, slug in PLAYER_ALIASES.items():
        if alias in request.question and slug in available and slug not in matched:
            matched.append(slug)

    if len(matched) < 2:
        raise AgentInputError("请在问题中明确提到两名球员，或使用球员选择器")
    return matched[:2]


def _build_metrics(
    selected: list[PlayerSnapshot],
    population: list[PlayerSnapshot],
    focus: AgentFocus,
) -> tuple[list[AgentMetricComparison], dict[str, int]]:
    weights = FOCUS_WEIGHTS[focus]
    scores = {item.player.slug: 0.0 for item in selected}
    comparisons: list[AgentMetricComparison] = []

    for key, weight in weights.items():
        population_values = [item.per90[key] for item in population]
        values = [
            AgentMetricValue(
                player_slug=item.player.slug,
                value=item.per90[key],
                percentile=percentile_rank(
                    item.per90[key],
                    population_values,
                ),
            )
            for item in selected
        ]
        for value in values:
            scores[value.player_slug] += value.percentile * weight

        raw_values = [value.value for value in values]
        leader = None
        if abs(raw_values[0] - raw_values[1]) >= 0.01:
            leader = values[raw_values.index(max(raw_values))].player_slug

        label, unit = METRICS[key]
        comparisons.append(
            AgentMetricComparison(
                key=key,
                label=label,
                unit=unit,
                weight=weight,
                values=values,
                leader_slug=leader,
            )
        )

    return comparisons, {slug: round(value) for slug, value in scores.items()}


def _build_evidence(
    metrics: list[AgentMetricComparison],
    names: dict[str, str],
) -> list[AgentEvidence]:
    ranked = sorted(
        metrics,
        key=lambda item: abs(item.values[0].percentile - item.values[1].percentile)
        * item.weight,
        reverse=True,
    )
    evidence: list[AgentEvidence] = []
    for metric in ranked[:3]:
        first, second = metric.values
        if metric.leader_slug is None:
            detail = (
                f"两人的{metric.label}均为 {first.value:.2f}，"
                "当前合格球员池下没有明显差距。"
            )
        else:
            leader = next(
                value
                for value in metric.values
                if value.player_slug == metric.leader_slug
            )
            other = next(
                value
                for value in metric.values
                if value.player_slug != metric.leader_slug
            )
            detail = (
                f"{names[leader.player_slug]}为 {leader.value:.2f}，"
                f"{names[other.player_slug]}为 {other.value:.2f}；"
                f"合格球员池百分位分别为 {leader.percentile} 和 "
                f"{other.percentile}。"
            )
        evidence.append(
            AgentEvidence(
                title=f"{metric.label}对比",
                detail=detail,
                leader_slug=metric.leader_slug,
            )
        )
    return evidence


def analyze_players(
    db: Session,
    request: AgentAnalysisRequest,
) -> AgentAnalysisData:
    population = load_player_snapshots(
        db,
        request.season,
        DEFAULT_MINIMUM_MINUTES,
    )
    if len(population) < 2:
        raise AgentInputError("当前赛季没有足够的合格球员记录用于比较")

    slugs = _resolve_player_slugs(request, population)
    by_slug = {item.player.slug: item for item in population}
    selected = [by_slug[slug] for slug in slugs]
    resolved_focus = _resolve_focus(request)
    metrics, scores = _build_metrics(
        selected,
        population,
        resolved_focus,
    )
    names = {item.player.slug: item.player.full_name for item in selected}

    winner_slug = max(scores, key=scores.get)
    loser_slug = next(slug for slug in slugs if slug != winner_slug)
    score_gap = abs(scores[winner_slug] - scores[loser_slug])
    confidence = round(min(0.82, 0.58 + score_gap / 250), 2)
    focus_label = FOCUS_LABELS[resolved_focus]

    limitations = [
        "数据未包含伤病、对手强度、比赛状态和具体战术角色。",
        "百分位只在达到 450 分钟的固定球员—球队记录池内计算，不能"
        "等同于绝对能力排名。",
    ]
    if selected[0].player.position != selected[1].player.position:
        limitations.append("两名球员登记位置不同，结论应结合实际场上职责理解。")

    return AgentAnalysisData(
        run_id=f"run_{uuid4().hex[:10]}",
        task_type="player_comparison",
        question=request.question,
        season=request.season,
        requested_focus=request.focus,
        focus=resolved_focus,
        focus_label=focus_label,
        players=[
            AgentPlayerProfile(
                slug=item.player.slug,
                full_name=item.player.full_name,
                club_name=item.player.club.short_name,
                club_color=item.player.club.primary_color,
                position=item.player.position,
                minutes=item.stats.minutes,
                nationality=item.player.nationality,
            )
            for item in selected
        ],
        steps=[
            AgentStep(
                index=1,
                title="理解任务",
                tool="intent_router",
                detail=(
                    "从任务描述自动识别"
                    if request.focus == "auto"
                    else "使用用户指定的分析重点"
                )
                + f"“{focus_label}”，并锁定双球员比较任务。",
                status="completed",
            ),
            AgentStep(
                index=2,
                title="读取赛季数据",
                tool="player_stats_query",
                detail=(
                    f"从数据库定位 {names[slugs[0]]} 与 {names[slugs[1]]} "
                    f"的 {request.season} 赛季记录。"
                ),
                status="completed",
            ),
            AgentStep(
                index=3,
                title="统一指标口径",
                tool="per90_calculator",
                detail=(
                    "将累计数据换算为每90分钟指标，并在达到 450 分钟的"
                    "固定球员池中计算百分位。"
                ),
                status="completed",
            ),
            AgentStep(
                index=4,
                title="生成决策建议",
                tool="evidence_ranker",
                detail="按任务权重汇总指标，只使用可追溯数据形成结论。",
                status="completed",
            ),
        ],
        metrics=metrics,
        evidence=_build_evidence(metrics, names),
        recommendation=AgentRecommendation(
            winner_slug=winner_slug,
            headline=f"{names[winner_slug]}更适合本次“{focus_label}”任务",
            summary=(
                f"Agent 综合得分 {scores[winner_slug]} 对 {scores[loser_slug]}。"
                "该建议来自每90分钟数据与合格球员池百分位加权，不代表"
                "绝对能力排名。"
            ),
            confidence=confidence,
            scores=scores,
        ),
        generation=AgentGeneration(
            mode="local_rules",
            status="pending",
            provider="local",
            model=None,
            note="等待回答生成层处理。",
        ),
        limitations=limitations,
        sample_notice=SAMPLE_NOTICE,
    )
