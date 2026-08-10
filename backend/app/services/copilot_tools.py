from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database.seed import (
    MATCH_SOURCE_KIND,
    SAMPLE_SEASON,
    SEASON_RESULTS_SOURCE_KIND,
    load_match_snapshot,
    load_season_results_snapshot,
)
from app.models import Club, Match, MatchEvent, Player, Standing
from app.schemas.agent import AgentAnalysisRequest, AgentFocus
from app.schemas.copilot import (
    CopilotEvidence,
    CopilotLink,
    CopilotSource,
    CopilotToolCapability,
    CopilotToolName,
    CopilotToolTrace,
)
from app.services.analysis_agent import (
    FOCUS_LABELS,
    PLAYER_ALIASES,
    AgentInputError,
    analyze_players,
)
from app.services.season_form import (
    build_record,
    longest_unbeaten_run,
    recent_form,
)


class CopilotToolError(ValueError):
    """Raised when a tool call is unknown, invalid, or outside the snapshot."""


class LeagueTableArguments(BaseModel):
    season: str = Field(default=SAMPLE_SEASON, pattern=r"^\d{4}-\d{2}$")
    limit: int = Field(default=5, ge=1, le=20)
    club: str | None = Field(default=None, max_length=120)


class ClubFormArguments(BaseModel):
    club: str = Field(min_length=2, max_length=120)
    season: str = Field(default=SAMPLE_SEASON, pattern=r"^\d{4}-\d{2}$")
    recent_matches: int = Field(default=5, ge=1, le=10)


class PlayerCompareArguments(BaseModel):
    player_a: str = Field(min_length=2, max_length=120)
    player_b: str = Field(min_length=2, max_length=120)
    season: str = Field(default=SAMPLE_SEASON, pattern=r"^\d{4}-\d{2}$")
    focus: AgentFocus = "balanced"


class MatchShotArguments(BaseModel):
    source_match_id: str = Field(default="3749448", min_length=1, max_length=40)


@dataclass(frozen=True)
class CopilotToolResult:
    trace: CopilotToolTrace
    payload: dict[str, Any]
    links: list[CopilotLink]
    limitations: list[str]


TOOL_CAPABILITIES = [
    CopilotToolCapability(
        name="get_league_table",
        label="最终积分榜",
        description="查询 2024-25 英超最终排名、积分与进失球。",
        data_scope="2024-25 最终 20 队历史快照",
    ),
    CopilotToolCapability(
        name="get_club_form",
        label="球队赛季状态",
        description="查询球队主客场拆分、近况与最长不败。",
        data_scope="2024-25 完整 38 场比分计算结果",
    ),
    CopilotToolCapability(
        name="compare_players",
        label="球员证据比较",
        description="比较两名样例球员的每90指标、百分位与加权得分。",
        data_scope="2024-25 共 12 名球员演示样例",
    ),
    CopilotToolCapability(
        name="get_match_shot_summary",
        label="单场射门复盘",
        description="查询公开历史比赛的射门数、进球与 xG。",
        data_scope="2003-04 Arsenal 4–2 Liverpool 单场事件快照",
    ),
]


TOOL_LABELS: dict[CopilotToolName, str] = {
    item.name: item.label for item in TOOL_CAPABILITIES
}


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_league_table",
            "description": (
                "查询 2024-25 英超最终积分榜。适用于排名、积分、冠军、"
                "欧冠区或降级区问题；club 可传球队中英文名或 slug。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "season": {"type": "string", "enum": [SAMPLE_SEASON]},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    "club": {"type": "string"},
                },
                "required": ["season"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_club_form",
            "description": (
                "查询一支球队在 2024-25 的主客场战绩、最近比赛状态、"
                "最终排名与最长不败；比较两队时分别调用两次。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "club": {"type": "string"},
                    "season": {"type": "string", "enum": [SAMPLE_SEASON]},
                    "recent_matches": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["club", "season"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_players",
            "description": (
                "比较两名球员的每90分钟指标与样例百分位。focus 仅支持"
                " balanced、scoring、creativity、pressing。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "player_a": {"type": "string"},
                    "player_b": {"type": "string"},
                    "season": {"type": "string", "enum": [SAMPLE_SEASON]},
                    "focus": {
                        "type": "string",
                        "enum": [
                            "balanced",
                            "scoring",
                            "creativity",
                            "pressing",
                        ],
                    },
                },
                "required": ["player_a", "player_b", "season", "focus"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_match_shot_summary",
            "description": (
                "查询 Arsenal 4–2 Liverpool（2004-04-09）公开事件快照"
                "中的射门、进球与 xG。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "source_match_id": {
                        "type": "string",
                        "enum": ["3749448"],
                    }
                },
                "required": ["source_match_id"],
            },
        },
    },
]


CLUB_ALIASES = {
    "阿森纳": "arsenal",
    "枪手": "arsenal",
    "维拉": "aston-villa",
    "阿斯顿维拉": "aston-villa",
    "伯恩茅斯": "afc-bournemouth",
    "布伦特福德": "brentford",
    "布莱顿": "brighton-and-hove-albion",
    "切尔西": "chelsea",
    "水晶宫": "crystal-palace",
    "埃弗顿": "everton",
    "富勒姆": "fulham",
    "伊普斯维奇": "ipswich-town",
    "莱斯特城": "leicester-city",
    "利物浦": "liverpool",
    "曼城": "manchester-city",
    "曼彻斯特城": "manchester-city",
    "曼联": "manchester-united",
    "曼彻斯特联": "manchester-united",
    "纽卡": "newcastle-united",
    "纽卡斯尔": "newcastle-united",
    "诺丁汉森林": "nottingham-forest",
    "森林": "nottingham-forest",
    "南安普顿": "southampton",
    "热刺": "tottenham-hotspur",
    "托特纳姆热刺": "tottenham-hotspur",
    "西汉姆": "west-ham-united",
    "西汉姆联": "west-ham-united",
    "狼队": "wolverhampton-wanderers",
}

EXTRA_PLAYER_ALIASES = {
    "范戴克": "virgil-van-dijk",
    "布鲁诺吉马良斯": "bruno-guimaraes",
    "吉马良斯": "bruno-guimaraes",
    "沃特金斯": "ollie-watkins",
    "蒂勒曼斯": "youri-tielemans",
}

STANDINGS_SOURCE = CopilotSource(
    name="Premier League 2024/25 table",
    url=(
        "https://www.premierleague.com/en/tables/premier-league/"
        "2024-25/all-matchweeks"
    ),
    data_scope="2024-25 最终积分榜历史快照",
)
FORM_SNAPSHOT = load_season_results_snapshot()
FORM_SOURCE = CopilotSource(
    name=FORM_SNAPSHOT["source"]["name"],
    url=FORM_SNAPSHOT["source"]["data_url"],
    license_name=FORM_SNAPSHOT["source"]["license_name"],
    license_url=FORM_SNAPSHOT["source"]["license_url"],
    data_scope="2024-25 完整 380 场最终比分快照",
)
PLAYER_SOURCE = CopilotSource(
    name="2024-25 球员演示样例",
    url=(
        "https://github.com/ruiyangxie434-byte/"
        "premier-league-insight-agent/blob/main/docs/DATA_SOURCES.md"
    ),
    data_scope="12 名球员样例与后端计算的每90分钟指标",
)
MATCH_SNAPSHOT = load_match_snapshot()
MATCH_SOURCE = CopilotSource(
    name=MATCH_SNAPSHOT["source"]["name"],
    url=MATCH_SNAPSHOT["source"]["events_url"],
    license_name="StatsBomb Open Data License",
    license_url=MATCH_SNAPSHOT["source"]["license_url"],
    data_scope="2003-04 Arsenal 4–2 Liverpool 单场射门事件",
)


def _normalize(value: str) -> str:
    return re.sub(r"[^\w]+", "", value.casefold(), flags=re.UNICODE)


def _require_season(season: str) -> None:
    if season != SAMPLE_SEASON:
        raise CopilotToolError("当前 Copilot 只支持 2024-25 赛季快照")


def _resolve_club(db: Session, value: str) -> Club:
    normalized = _normalize(value)
    alias_slug = next(
        (
            slug
            for alias, slug in CLUB_ALIASES.items()
            if _normalize(alias) == normalized
        ),
        None,
    )
    clubs = list(db.scalars(select(Club).order_by(Club.name)).all())
    if alias_slug is not None:
        match = next((club for club in clubs if club.slug == alias_slug), None)
        if match is not None:
            return match

    exact = [
        club
        for club in clubs
        if normalized
        in {
            _normalize(club.slug),
            _normalize(club.name),
            _normalize(club.short_name),
        }
    ]
    if len(exact) == 1:
        return exact[0]

    partial = [
        club
        for club in clubs
        if len(normalized) >= 4
        and any(
            normalized in candidate or candidate in normalized
            for candidate in (
                _normalize(club.slug),
                _normalize(club.name),
                _normalize(club.short_name),
            )
        )
    ]
    if len(partial) == 1:
        return partial[0]
    raise CopilotToolError(f"没有唯一匹配到球队：{value}")


def _resolve_player(db: Session, value: str) -> Player:
    normalized = _normalize(value)
    aliases = {**PLAYER_ALIASES, **EXTRA_PLAYER_ALIASES}
    alias_slug = next(
        (
            slug
            for alias, slug in aliases.items()
            if _normalize(alias) == normalized
        ),
        None,
    )
    players = list(
        db.scalars(
            select(Player).options(joinedload(Player.club)).order_by(Player.full_name)
        ).unique().all()
    )
    if alias_slug is not None:
        match = next((player for player in players if player.slug == alias_slug), None)
        if match is not None:
            return match

    exact = [
        player
        for player in players
        if normalized
        in {
            _normalize(player.slug),
            _normalize(player.full_name),
            _normalize(player.full_name.split()[-1]),
        }
    ]
    if len(exact) == 1:
        return exact[0]
    raise CopilotToolError(f"没有唯一匹配到球员：{value}")


def find_club_mentions(db: Session, question: str) -> list[str]:
    folded = question.casefold()
    mentions: list[tuple[int, str]] = []
    for alias, slug in CLUB_ALIASES.items():
        index = folded.find(alias.casefold())
        if index >= 0:
            mentions.append((index, slug))
    for club in db.scalars(select(Club).order_by(Club.name)).all():
        for candidate in (club.name, club.short_name, club.slug.replace("-", " ")):
            index = folded.find(candidate.casefold())
            if index >= 0:
                mentions.append((index, club.slug))
    ordered: list[str] = []
    for _, slug in sorted(mentions, key=lambda item: (item[0], -len(item[1]))):
        if slug not in ordered:
            ordered.append(slug)
    return ordered


def find_player_mentions(db: Session, question: str) -> list[str]:
    folded = question.casefold()
    mentions: list[tuple[int, str]] = []
    for alias, slug in {**PLAYER_ALIASES, **EXTRA_PLAYER_ALIASES}.items():
        index = folded.find(alias.casefold())
        if index >= 0:
            mentions.append((index, slug))
    for player in db.scalars(select(Player).order_by(Player.full_name)).all():
        for candidate in (
            player.full_name,
            player.full_name.split()[-1],
            player.slug.replace("-", " "),
        ):
            index = folded.find(candidate.casefold())
            if index >= 0:
                mentions.append((index, player.slug))
    ordered: list[str] = []
    for _, slug in sorted(mentions, key=lambda item: (item[0], -len(item[1]))):
        if slug not in ordered:
            ordered.append(slug)
    return ordered


def _trace(
    *,
    call_id: str,
    tool: CopilotToolName,
    arguments: BaseModel,
    summary: str,
    evidence: list[CopilotEvidence],
    source: CopilotSource,
) -> CopilotToolTrace:
    return CopilotToolTrace(
        index=0,
        call_id=call_id,
        tool=tool,
        label=TOOL_LABELS[tool],
        arguments=arguments.model_dump(exclude_none=True),
        summary=summary,
        evidence=evidence,
        source=source,
    )


def _get_league_table(
    db: Session,
    arguments: LeagueTableArguments,
    call_id: str,
) -> CopilotToolResult:
    _require_season(arguments.season)
    standings = list(
        db.scalars(
            select(Standing)
            .options(joinedload(Standing.club))
            .where(Standing.season == arguments.season)
            .order_by(Standing.position)
        ).unique().all()
    )
    if len(standings) != 20:
        raise CopilotToolError("最终积分榜快照尚未完整初始化")

    highlighted = _resolve_club(db, arguments.club) if arguments.club else None
    top = standings[: arguments.limit]
    evidence = [
        CopilotEvidence(
            label=f"第 {standing.position} 名",
            value=f"{standing.club.short_name} · {standing.points} 分",
            detail=(
                f"{standing.won}胜 {standing.drawn}平 {standing.lost}负，"
                f"净胜球 {standing.goal_difference:+d}。"
            ),
            tool="get_league_table",
        )
        for standing in top[:3]
    ]
    highlighted_row = next(
        (
            standing
            for standing in standings
            if highlighted is not None and standing.club_id == highlighted.id
        ),
        None,
    )
    if highlighted_row is not None and highlighted_row not in top[:3]:
        evidence.append(
            CopilotEvidence(
                label=f"{highlighted_row.club.short_name} 最终排名",
                value=f"第 {highlighted_row.position} 名 · {highlighted_row.points} 分",
                detail=(
                    f"进 {highlighted_row.goals_for} 球、失 "
                    f"{highlighted_row.goals_against} 球，净胜球 "
                    f"{highlighted_row.goal_difference:+d}。"
                ),
                tool="get_league_table",
            )
        )

    champion = standings[0]
    summary = (
        f"最终积分榜显示 {champion.club.short_name} 以 {champion.points} 分夺冠。"
    )
    if highlighted_row is not None:
        summary += (
            f" {highlighted_row.club.short_name} 位列第 "
            f"{highlighted_row.position}，得到 {highlighted_row.points} 分。"
        )

    return CopilotToolResult(
        trace=_trace(
            call_id=call_id,
            tool="get_league_table",
            arguments=arguments.model_copy(
                update={
                    "club": highlighted.slug if highlighted is not None else None
                }
            ),
            summary=summary,
            evidence=evidence,
            source=STANDINGS_SOURCE,
        ),
        payload={
            "season": arguments.season,
            "top": [
                {
                    "position": row.position,
                    "club": row.club.short_name,
                    "slug": row.club.slug,
                    "points": row.points,
                    "goal_difference": row.goal_difference,
                }
                for row in top
            ],
            "highlight": (
                {
                    "position": highlighted_row.position,
                    "club": highlighted_row.club.short_name,
                    "slug": highlighted_row.club.slug,
                    "points": highlighted_row.points,
                    "goal_difference": highlighted_row.goal_difference,
                }
                if highlighted_row is not None
                else None
            ),
        },
        links=[CopilotLink(label="打开赛季状态实验室", href="/form")],
        limitations=["积分榜是 2025-05-25 的赛季终态，不是实时排名。"],
    )


def _get_club_form(
    db: Session,
    arguments: ClubFormArguments,
    call_id: str,
) -> CopilotToolResult:
    _require_season(arguments.season)
    club = _resolve_club(db, arguments.club)
    standing = db.scalar(
        select(Standing).where(
            Standing.club_id == club.id,
            Standing.season == arguments.season,
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
                Match.season == arguments.season,
                Match.source_kind == SEASON_RESULTS_SOURCE_KIND,
                or_(
                    Match.home_club_id == club.id,
                    Match.away_club_id == club.id,
                ),
            )
            .order_by(Match.kickoff_at, Match.matchweek)
        ).all()
    )
    if standing is None or len(matches) != 38:
        raise CopilotToolError(f"{club.short_name} 的完整赛果尚未初始化")

    overall = build_record(matches, club.id)
    home = build_record(
        (match for match in matches if match.home_club_id == club.id),
        club.id,
    )
    away = build_record(
        (match for match in matches if match.away_club_id == club.id),
        club.id,
    )
    form = recent_form(matches, club.id, arguments.recent_matches)
    recent_points = sum(3 if item == "W" else 1 if item == "D" else 0 for item in form)
    form_label = "-".join(form)
    evidence = [
        CopilotEvidence(
            label=f"{club.short_name} 赛季终态",
            value=f"第 {standing.position} 名 · {overall.points} 分",
            detail=(
                f"{overall.won}胜 {overall.drawn}平 {overall.lost}负，"
                f"净胜球 {overall.goal_difference:+d}。"
            ),
            tool="get_club_form",
        ),
        CopilotEvidence(
            label="主客场每场积分",
            value=f"主 {home.points_per_game:.2f} / 客 {away.points_per_game:.2f}",
            detail=(
                f"主场 {home.won}胜 {home.drawn}平 {home.lost}负；"
                f"客场 {away.won}胜 {away.drawn}平 {away.lost}负。"
            ),
            tool="get_club_form",
        ),
        CopilotEvidence(
            label=f"最近 {arguments.recent_matches} 场",
            value=f"{form_label} · {recent_points} 分",
            detail=f"最长不败为 {longest_unbeaten_run(matches, club.id)} 场。",
            tool="get_club_form",
        ),
    ]
    summary = (
        f"{club.short_name} 最终第 {standing.position}、{overall.points} 分；"
        f"主场每场 {home.points_per_game:.2f} 分，客场每场 "
        f"{away.points_per_game:.2f} 分，最近 {arguments.recent_matches} 场为 "
        f"{form_label}。"
    )
    return CopilotToolResult(
        trace=_trace(
            call_id=call_id,
            tool="get_club_form",
            arguments=arguments.model_copy(update={"club": club.slug}),
            summary=summary,
            evidence=evidence,
            source=FORM_SOURCE,
        ),
        payload={
            "club": club.short_name,
            "slug": club.slug,
            "final_position": standing.position,
            "overall": overall.model_dump(),
            "home": home.model_dump(),
            "away": away.model_dump(),
            "recent_form": form,
            "recent_points": recent_points,
            "longest_unbeaten": longest_unbeaten_run(matches, club.id),
        },
        links=[
            CopilotLink(label=f"查看 {club.short_name} 球队页", href=f"/clubs/{club.slug}"),
            CopilotLink(label="打开赛季状态实验室", href="/form"),
        ],
        limitations=[
            "球队状态只由最终比分计算，不包含 xG、控球率、伤病或比赛过程。"
        ],
    )


def _compare_players(
    db: Session,
    arguments: PlayerCompareArguments,
    call_id: str,
) -> CopilotToolResult:
    _require_season(arguments.season)
    player_a = _resolve_player(db, arguments.player_a)
    player_b = _resolve_player(db, arguments.player_b)
    if player_a.slug == player_b.slug:
        raise CopilotToolError("请选择两名不同的球员")

    try:
        result = analyze_players(
            db,
            AgentAnalysisRequest(
                question=(
                    f"比较 {player_a.full_name} 和 {player_b.full_name} "
                    f"的{FOCUS_LABELS[arguments.focus]}表现"
                ),
                player_slugs=[player_a.slug, player_b.slug],
                season=arguments.season,
                focus=arguments.focus,
            ),
        )
    except AgentInputError as exc:
        raise CopilotToolError(str(exc)) from exc

    names = {player.slug: player.full_name for player in result.players}
    winner = names[result.recommendation.winner_slug]
    evidence = [
        CopilotEvidence(
            label=item.title,
            value=(names.get(item.leader_slug, "差距不明显") if item.leader_slug else "接近"),
            detail=item.detail,
            tool="compare_players",
        )
        for item in result.evidence
    ]
    evidence.insert(
        0,
        CopilotEvidence(
            label=f"{result.focus_label}综合得分",
            value=" / ".join(
                f"{names[slug]} {score}"
                for slug, score in result.recommendation.scores.items()
            ),
            detail=f"样例加权结果更支持 {winner}；该得分不是完整英超排名。",
            tool="compare_players",
        ),
    )
    summary = (
        f"在“{result.focus_label}”权重下，{result.recommendation.headline}。"
        f" {result.recommendation.summary}"
    )
    return CopilotToolResult(
        trace=_trace(
            call_id=call_id,
            tool="compare_players",
            arguments=arguments.model_copy(
                update={"player_a": player_a.slug, "player_b": player_b.slug}
            ),
            summary=summary,
            evidence=evidence,
            source=PLAYER_SOURCE,
        ),
        payload={
            "focus": result.focus,
            "focus_label": result.focus_label,
            "players": [player.model_dump() for player in result.players],
            "scores": result.recommendation.scores,
            "winner_slug": result.recommendation.winner_slug,
            "headline": result.recommendation.headline,
            "summary": result.recommendation.summary,
            "metrics": [metric.model_dump() for metric in result.metrics],
        },
        links=[
            CopilotLink(
                label="在 Agent Notebook 中继续比较",
                href=(
                    f"/?playerA={player_a.slug}&playerB={player_b.slug}"
                    "#analysis-agent"
                ),
            ),
            CopilotLink(label="打开球员实验室", href="/players"),
        ],
        limitations=[
            "当前比较只覆盖 12 名球员演示样例，百分位不是完整英超排名。",
            *result.limitations,
        ],
    )


def _get_match_shot_summary(
    db: Session,
    arguments: MatchShotArguments,
    call_id: str,
) -> CopilotToolResult:
    match = db.scalar(
        select(Match)
        .options(
            selectinload(Match.home_club),
            selectinload(Match.away_club),
            selectinload(Match.events).selectinload(MatchEvent.club),
        )
        .where(
            Match.source_match_id == arguments.source_match_id,
            Match.source_kind == MATCH_SOURCE_KIND,
        )
    )
    if match is None:
        raise CopilotToolError("当前只提供比赛 3749448 的公开事件快照")

    shots = [event for event in match.events if event.event_type == "shot"]
    teams: list[dict[str, Any]] = []
    evidence: list[CopilotEvidence] = []
    for club, score in (
        (match.home_club, match.home_score or 0),
        (match.away_club, match.away_score or 0),
    ):
        team_shots = [event for event in shots if event.club_id == club.id]
        total_xg = round(sum(event.xg or 0 for event in team_shots), 3)
        teams.append(
            {
                "club": club.short_name,
                "slug": club.slug,
                "score": score,
                "shots": len(team_shots),
                "xg": total_xg,
                "goals_minus_xg": round(score - total_xg, 3),
            }
        )
        evidence.append(
            CopilotEvidence(
                label=f"{club.short_name} 射门质量",
                value=f"{len(team_shots)} 次射门 · {total_xg:.3f} xG",
                detail=f"打进 {score} 球，Goals - xG 为 {score - total_xg:+.3f}。",
                tool="get_match_shot_summary",
            )
        )

    evidence.append(
        CopilotEvidence(
            label="全场事件覆盖",
            value=f"{len(shots)} 次射门 · {len([s for s in shots if s.outcome == 'Goal'])} 个进球",
            detail="坐标已统一到 0–100 进攻方向，仅代表射门位置。",
            tool="get_match_shot_summary",
        )
    )
    summary = (
        f"{match.home_club.short_name} {match.home_score}–{match.away_score} "
        f"{match.away_club.short_name} 共记录 {len(shots)} 次射门；"
        f"双方 xG 分别为 {teams[0]['xg']:.3f} 与 {teams[1]['xg']:.3f}。"
    )
    return CopilotToolResult(
        trace=_trace(
            call_id=call_id,
            tool="get_match_shot_summary",
            arguments=arguments,
            summary=summary,
            evidence=evidence,
            source=MATCH_SOURCE,
        ),
        payload={
            "source_match_id": match.source_match_id,
            "season": match.season,
            "home_team": match.home_club.short_name,
            "away_team": match.away_club.short_name,
            "home_score": match.home_score,
            "away_score": match.away_score,
            "shot_count": len(shots),
            "teams": teams,
        },
        links=[
            CopilotLink(
                label="打开完整射门图",
                href=f"/matches/{arguments.source_match_id}",
            )
        ],
        limitations=[
            "该工具只使用 2003-04 单场射门事件，不与 2024-25 赛季数据混算。",
            "xG 描述机会质量，不代表必然进球，也不能推断阵型或无球跑动。",
        ],
    )


def execute_copilot_tool(
    db: Session,
    *,
    name: str,
    arguments: dict[str, Any],
    call_id: str,
) -> CopilotToolResult:
    try:
        if name == "get_league_table":
            return _get_league_table(
                db,
                LeagueTableArguments.model_validate(arguments),
                call_id,
            )
        if name == "get_club_form":
            return _get_club_form(
                db,
                ClubFormArguments.model_validate(arguments),
                call_id,
            )
        if name == "compare_players":
            return _compare_players(
                db,
                PlayerCompareArguments.model_validate(arguments),
                call_id,
            )
        if name == "get_match_shot_summary":
            return _get_match_shot_summary(
                db,
                MatchShotArguments.model_validate(arguments),
                call_id,
            )
    except ValidationError as exc:
        first_error = exc.errors()[0]
        location = ".".join(str(part) for part in first_error["loc"])
        raise CopilotToolError(
            f"工具 {name} 参数 {location} 无效：{first_error['msg']}"
        ) from exc
    raise CopilotToolError(f"不允许调用未知工具：{name}")
