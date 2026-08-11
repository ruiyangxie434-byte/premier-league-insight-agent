from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import httpx
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.database.seed import SAMPLE_SEASON
from app.models import Club
from app.schemas.agent import AgentFocus
from app.schemas.copilot import (
    CopilotAnswerData,
    CopilotGeneration,
    CopilotLink,
    CopilotQueryRequest,
)
from app.services.copilot_tools import (
    TOOL_DEFINITIONS,
    CopilotToolError,
    CopilotToolResult,
    execute_copilot_tool,
    find_club_mentions,
    find_player_mentions,
)
from app.services.player_lab import DEFAULT_MINIMUM_MINUTES
from app.services.player_metrics import load_player_snapshots


class CopilotInputError(ValueError):
    """Raised when a question cannot be grounded in the available tools."""


class QwenCopilotError(RuntimeError):
    """Raised when Qwen does not return a safe, valid tool plan or narrative."""


class QwenCopilotNarrative(BaseModel):
    headline: str = Field(min_length=4, max_length=120)
    answer: str = Field(min_length=20, max_length=900)


@dataclass(frozen=True)
class PlannedToolCall:
    call_id: str
    name: str
    arguments: dict[str, Any]


SCOPE_NOTICE = (
    "Copilot 只访问项目内的历史快照：2024-25 最终积分榜与 380 场比分、"
    "574 条球员—球队记录（比较工具使用其中 400 条 450+ 分钟记录），"
    "以及 2003-04 Arsenal 4–2 Liverpool 单场事件；"
    "不联网查询实时新闻、伤病、转会或比分。"
)

PLANNER_SYSTEM_PROMPT = """
你是“英超智析 League Copilot”的工具规划器。
你不能直接回答足球问题，只能从提供的受控函数中选择工具。

规则：
1. 每个事实都必须来自工具；不得使用训练记忆补充实时新闻、伤病、转会或赛果。
2. 2024-25 只可用于最终积分榜、完整赛果和固定球员历史快照。
   同名跨队球员必须使用俱乐部或完整 slug 消除歧义。
3. 2003-04 只可用于 source_match_id=3749448 的单场射门事件，不能与 2024-25 混算。
4. 比较两支球队时，可以分别调用两次 get_club_form；同时询问排名时再调用 get_league_table。
5. 最多调用四个工具。参数使用工具声明允许的值。
6. 问题超出数据范围时不要编造工具。
""".strip()

NARRATIVE_SYSTEM_PROMPT = """
你是“英超智析 League Copilot”的证据表达层。
后端已经执行受控工具并返回结构化事实。只能根据这些工具输出组织中文回答。

必须遵守：
1. 不补充工具输出之外的足球事实，不使用实时知识。
2. 不改变球队排名、积分、比分、xG、球员得分或数据赛季。
3. 明确区分 2024-25 赛季快照与 2003-04 单场事件。
4. 结论简洁、可核查，避免“绝对更强”等绝对化措辞。
5. 只返回 JSON 对象，字段必须为 headline 和 answer。
""".strip()

STANDINGS_KEYWORDS = (
    "积分榜",
    "排名",
    "第几",
    "冠军",
    "降级",
    "前四",
    "欧冠区",
    "table",
    "rank",
    "points",
)
FORM_KEYWORDS = (
    "状态",
    "近期",
    "最近",
    "近五场",
    "近况",
    "主场",
    "客场",
    "不败",
    "连胜",
    "表现",
    "form",
    "home",
    "away",
)
COMPARISON_KEYWORDS = ("对比", "比较", "差异", "谁更", "哪个好")


def _focus_from_question(question: str) -> AgentFocus:
    folded = question.casefold()
    keywords: dict[AgentFocus, tuple[str, ...]] = {
        "scoring": ("进球", "终结", "射门", "得分", "xg"),
        "creativity": ("创造", "组织", "助攻", "关键传球", "机会"),
        "pressing": ("逼抢", "压迫", "抢断", "拦截", "防守", "反抢"),
        "balanced": ("综合", "全面", "整体", "攻防"),
    }
    scores = {
        focus: sum(keyword in folded for keyword in values)
        for focus, values in keywords.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] else "balanced"


def build_local_tool_plan(
    db: Session,
    request: CopilotQueryRequest,
) -> list[PlannedToolCall]:
    if request.season != SAMPLE_SEASON:
        raise CopilotInputError("当前 Copilot 只支持 2024-25 赛季快照")

    folded = request.question.casefold()
    clubs = find_club_mentions(db, request.question)
    players = find_player_mentions(db, request.question)
    calls: list[PlannedToolCall] = []

    def add(name: str, arguments: dict[str, Any]) -> None:
        signature = (name, json.dumps(arguments, sort_keys=True, ensure_ascii=False))
        existing = {
            (item.name, json.dumps(item.arguments, sort_keys=True, ensure_ascii=False))
            for item in calls
        }
        if signature not in existing and len(calls) < 4:
            calls.append(
                PlannedToolCall(
                    call_id=f"local_{len(calls) + 1}",
                    name=name,
                    arguments=arguments,
                )
            )

    asks_for_historical_match = (
        "2004" in folded
        or "3749448" in folded
        or (
            ("arsenal" in folded or "阿森纳" in folded)
            and ("liverpool" in folded or "利物浦" in folded)
            and any(
                keyword in folded
                for keyword in ("xg", "射门", "shot", "4-2", "4–2", "比赛复盘")
            )
        )
    )
    if asks_for_historical_match:
        add("get_match_shot_summary", {"source_match_id": "3749448"})
        return calls

    if len(players) >= 2:
        add(
            "compare_players",
            {
                "player_a": players[0],
                "player_b": players[1],
                "season": request.season,
                "focus": _focus_from_question(request.question),
            },
        )

    asks_for_table = any(keyword in folded for keyword in STANDINGS_KEYWORDS)
    asks_for_form = any(keyword in folded for keyword in FORM_KEYWORDS)
    compares_clubs = (
        len(clubs) >= 2
        and any(keyword in folded for keyword in COMPARISON_KEYWORDS)
    )
    if asks_for_table:
        add(
            "get_league_table",
            {
                "season": request.season,
                "limit": 5 if not clubs else 20,
                **({"club": clubs[0]} if len(clubs) == 1 else {}),
            },
        )
    if clubs and (asks_for_form or compares_clubs or not asks_for_table):
        for club in clubs[:2]:
            add(
                "get_club_form",
                {
                    "club": club,
                    "season": request.season,
                    "recent_matches": 5,
                },
            )

    if not calls:
        raise CopilotInputError(
            "当前问题无法落到可用数据工具。请询问积分榜、球队状态、"
            "两名 450+ 分钟球员记录的比较，或 2004 年 Arsenal 4–2 "
            "Liverpool 的射门；同名跨队记录请同时写明俱乐部。"
        )
    return calls


def _entity_context(db: Session) -> dict[str, list[dict[str, str]]]:
    player_snapshots = load_player_snapshots(
        db,
        SAMPLE_SEASON,
        DEFAULT_MINIMUM_MINUTES,
    )
    return {
        "clubs": [
            {"name": club.name, "short_name": club.short_name, "slug": club.slug}
            for club in db.scalars(select(Club).order_by(Club.name)).all()
        ],
        "players": [
            {
                "name": item.player.full_name,
                "slug": item.player.slug,
                "club": item.player.club.short_name,
            }
            for item in player_snapshots
        ],
    }


def _post_qwen(
    settings: Settings,
    request_body: dict[str, Any],
    client: httpx.Client | None,
) -> dict[str, Any]:
    if not settings.qwen_configured:
        raise QwenCopilotError("Qwen is not configured")
    endpoint = f"{settings.qwen_base_url.rstrip('/')}/chat/completions"
    owns_client = client is None
    active_client = client or httpx.Client(timeout=settings.qwen_timeout_seconds)
    try:
        response = active_client.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {settings.dashscope_api_key}",
                "Content-Type": "application/json",
            },
            json=request_body,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise QwenCopilotError("Qwen returned a non-object response")
        return payload
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        raise QwenCopilotError("Qwen request failed") from exc
    finally:
        if owns_client:
            active_client.close()


def request_qwen_tool_plan(
    db: Session,
    request: CopilotQueryRequest,
    settings: Settings,
    client: httpx.Client | None = None,
) -> list[PlannedToolCall]:
    payload = _post_qwen(
        settings,
        {
            "model": settings.qwen_model,
            "messages": [
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "question": request.question,
                            "season": request.season,
                            "available_entities": _entity_context(db),
                            "scope_notice": SCOPE_NOTICE,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "tools": TOOL_DEFINITIONS,
            "tool_choice": "auto",
            "temperature": 0,
        },
        client,
    )
    try:
        message = payload["choices"][0]["message"]
        raw_calls = message["tool_calls"]
        if not isinstance(raw_calls, list) or not raw_calls:
            raise QwenCopilotError("Qwen did not select a tool")
        if len(raw_calls) > 4:
            raise QwenCopilotError("Qwen selected too many tools")

        calls: list[PlannedToolCall] = []
        for index, raw_call in enumerate(raw_calls, start=1):
            function = raw_call["function"]
            name = function["name"]
            raw_arguments = function.get("arguments", "{}")
            arguments = (
                json.loads(raw_arguments)
                if isinstance(raw_arguments, str)
                else raw_arguments
            )
            if not isinstance(name, str) or not isinstance(arguments, dict):
                raise QwenCopilotError("Qwen returned invalid tool arguments")
            calls.append(
                PlannedToolCall(
                    call_id=str(raw_call.get("id") or f"qwen_{index}"),
                    name=name,
                    arguments=arguments,
                )
            )
        return calls
    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise QwenCopilotError("Qwen returned an invalid tool plan") from exc


def request_qwen_narrative(
    request: CopilotQueryRequest,
    results: list[CopilotToolResult],
    settings: Settings,
    client: httpx.Client | None = None,
) -> QwenCopilotNarrative:
    grounding = {
        "question": request.question,
        "season": request.season,
        "tool_results": [
            {
                "tool": result.trace.tool,
                "arguments": result.trace.arguments,
                "summary": result.trace.summary,
                "payload": result.payload,
                "source": result.trace.source.model_dump(),
                "limitations": result.limitations,
            }
            for result in results
        ],
        "scope_notice": SCOPE_NOTICE,
    }
    payload = _post_qwen(
        settings,
        {
            "model": settings.qwen_model,
            "messages": [
                {"role": "system", "content": NARRATIVE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(grounding, ensure_ascii=False),
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        },
        client,
    )
    try:
        content = payload["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise QwenCopilotError("Qwen returned empty narrative")
        return QwenCopilotNarrative.model_validate_json(content)
    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        ValidationError,
    ) as exc:
        raise QwenCopilotError("Qwen returned an invalid narrative") from exc


def _local_narrative(
    request: CopilotQueryRequest,
    results: list[CopilotToolResult],
) -> QwenCopilotNarrative:
    tools = [result.trace.tool for result in results]
    form_results = [
        result for result in results if result.trace.tool == "get_club_form"
    ]

    if tools == ["compare_players"]:
        payload = results[0].payload
        return QwenCopilotNarrative(
            headline=str(payload["headline"]),
            answer=results[0].trace.summary,
        )
    if tools == ["get_match_shot_summary"]:
        payload = results[0].payload
        return QwenCopilotNarrative(
            headline=(
                f"{payload['home_team']} {payload['home_score']}–"
                f"{payload['away_score']} {payload['away_team']}：射门与 xG 复盘"
            ),
            answer=results[0].trace.summary,
        )
    if len(form_results) >= 2:
        first, second = form_results[:2]
        first_data, second_data = first.payload, second.payload
        if first_data["overall"]["points"] == second_data["overall"]["points"]:
            comparison = "两队赛季积分相同。"
        else:
            leader = max(
                (first_data, second_data),
                key=lambda item: item["overall"]["points"],
            )
            gap = abs(
                first_data["overall"]["points"]
                - second_data["overall"]["points"]
            )
            comparison = f"{leader['club']} 的赛季积分高出 {gap} 分。"
        return QwenCopilotNarrative(
            headline=f"{first_data['club']} vs {second_data['club']}：赛季状态对照",
            answer=" ".join(
                [
                    comparison,
                    first.trace.summary,
                    second.trace.summary,
                ]
            ),
        )
    if form_results:
        data = form_results[0].payload
        return QwenCopilotNarrative(
            headline=f"{data['club']}：2024-25 赛季状态",
            answer=form_results[0].trace.summary,
        )
    if "get_league_table" in tools:
        table = next(
            result for result in results if result.trace.tool == "get_league_table"
        )
        return QwenCopilotNarrative(
            headline="2024-25 英超最终积分榜",
            answer=table.trace.summary,
        )

    return QwenCopilotNarrative(
        headline="League Copilot 已完成受控查询",
        answer=" ".join(result.trace.summary for result in results),
    )


def _suggestions(results: list[CopilotToolResult]) -> list[str]:
    tools = {result.trace.tool for result in results}
    suggestions: list[str] = []
    if "get_league_table" in tools or "get_club_form" in tools:
        suggestions.append("比较利物浦和阿森纳的主客场表现与最近五场状态")
    if "compare_players" not in tools:
        suggestions.append("萨卡和帕尔默谁更适合承担创造任务？")
    if "get_match_shot_summary" not in tools:
        suggestions.append("2004 年 Arsenal 4–2 Liverpool 的射门质量如何？")
    if "get_league_table" not in tools:
        suggestions.append("2024-25 英超积分榜前三名是谁？")
    return suggestions[:3]


def _unique_links(results: list[CopilotToolResult]) -> list[CopilotLink]:
    links: list[CopilotLink] = []
    seen: set[str] = set()
    for result in results:
        for link in result.links:
            if link.href not in seen:
                links.append(link)
                seen.add(link.href)
    return links


def _unique_limitations(results: list[CopilotToolResult]) -> list[str]:
    limitations: list[str] = []
    for result in results:
        for limitation in result.limitations:
            if limitation not in limitations:
                limitations.append(limitation)
    return limitations


def _execute_plan(
    db: Session,
    calls: list[PlannedToolCall],
) -> list[CopilotToolResult]:
    results: list[CopilotToolResult] = []
    for index, call in enumerate(calls, start=1):
        result = execute_copilot_tool(
            db,
            name=call.name,
            arguments=call.arguments,
            call_id=call.call_id,
        )
        trace = result.trace.model_copy(update={"index": index})
        results.append(
            CopilotToolResult(
                trace=trace,
                payload=result.payload,
                links=result.links,
                limitations=result.limitations,
            )
        )
    return results


def _qwen_plan_matches_question_scope(
    expected: list[PlannedToolCall],
    results: list[CopilotToolResult],
) -> bool:
    expected_counts = Counter(call.name for call in expected)
    actual_counts = Counter(result.trace.tool for result in results)
    if expected_counts != actual_counts:
        return False

    expected_forms = {
        (
            str(call.arguments["club"]),
            int(call.arguments["recent_matches"]),
        )
        for call in expected
        if call.name == "get_club_form"
    }
    actual_forms = {
        (
            str(result.trace.arguments["club"]),
            int(result.trace.arguments["recent_matches"]),
        )
        for result in results
        if result.trace.tool == "get_club_form"
    }
    if expected_forms != actual_forms:
        return False

    expected_players = {
        str(value)
        for call in expected
        if call.name == "compare_players"
        for key, value in call.arguments.items()
        if key in {"player_a", "player_b"}
    }
    actual_players = {
        str(value)
        for result in results
        if result.trace.tool == "compare_players"
        for key, value in result.trace.arguments.items()
        if key in {"player_a", "player_b"}
    }
    if expected_players != actual_players:
        return False

    expected_focuses = {
        str(call.arguments["focus"])
        for call in expected
        if call.name == "compare_players"
    }
    actual_focuses = {
        str(result.trace.arguments["focus"])
        for result in results
        if result.trace.tool == "compare_players"
    }
    if expected_focuses != actual_focuses:
        return False

    expected_table_clubs = {
        str(call.arguments["club"])
        for call in expected
        if call.name == "get_league_table" and call.arguments.get("club")
    }
    actual_table_clubs = {
        str(result.trace.arguments["club"])
        for result in results
        if result.trace.tool == "get_league_table"
        and result.trace.arguments.get("club")
    }
    if expected_table_clubs != actual_table_clubs:
        return False

    expected_matches = {
        str(call.arguments["source_match_id"])
        for call in expected
        if call.name == "get_match_shot_summary"
    }
    actual_matches = {
        str(result.trace.arguments["source_match_id"])
        for result in results
        if result.trace.tool == "get_match_shot_summary"
    }
    return expected_matches == actual_matches


def run_league_copilot(
    db: Session,
    request: CopilotQueryRequest,
    settings: Settings,
    client: httpx.Client | None = None,
) -> CopilotAnswerData:
    qwen_planned = False
    planner_fallback = False
    safe_plan = build_local_tool_plan(db, request)

    if settings.qwen_configured:
        try:
            calls = request_qwen_tool_plan(db, request, settings, client=client)
            results = _execute_plan(db, calls)
            if not _qwen_plan_matches_question_scope(safe_plan, results):
                raise QwenCopilotError(
                    "Qwen tool plan does not match the supported question scope"
                )
            qwen_planned = True
        except (QwenCopilotError, CopilotToolError):
            planner_fallback = True
            calls = safe_plan
            results = _execute_plan(db, safe_plan)
    else:
        calls = safe_plan
        results = _execute_plan(db, safe_plan)

    local_narrative = _local_narrative(request, results)
    narrative = local_narrative
    narrative_fallback = False
    if qwen_planned:
        try:
            narrative = request_qwen_narrative(
                request,
                results,
                settings,
                client=client,
            )
        except QwenCopilotError:
            narrative_fallback = True

    if qwen_planned and not narrative_fallback:
        generation = CopilotGeneration(
            mode="qwen_tool_calling",
            status="completed",
            provider="qwen",
            model=settings.qwen_model,
            note="千问选择受控工具，后端执行并校验参数后，千问只组织工具返回的证据。",
        )
    elif qwen_planned:
        generation = CopilotGeneration(
            mode="qwen_tool_calling",
            status="fallback",
            provider="qwen",
            model=settings.qwen_model,
            note="千问已选择并调用工具；回答组织失败后使用本地证据模板完成。",
        )
    elif settings.qwen_configured and planner_fallback:
        generation = CopilotGeneration(
            mode="local_tool_router",
            status="fallback",
            provider="qwen",
            model=settings.qwen_model,
            note="千问工具计划不可用，系统已切换至同一受控工具层的本地路由。",
        )
    else:
        generation = CopilotGeneration(
            mode="local_tool_router",
            status="not_configured",
            provider="local",
            model=None,
            note="未配置千问 API Key；本地路由仍会执行真实数据库工具并保留完整轨迹。",
        )

    evidence = [
        item
        for result in results
        for item in result.trace.evidence
    ]
    return CopilotAnswerData(
        run_id=f"copilot_{uuid4().hex[:10]}",
        question=request.question,
        season=request.season,
        headline=narrative.headline,
        answer=narrative.answer,
        generation=generation,
        tool_calls=[result.trace for result in results],
        evidence=evidence,
        links=_unique_links(results),
        limitations=_unique_limitations(results),
        suggestions=_suggestions(results),
        scope_notice=SCOPE_NOTICE,
    )
