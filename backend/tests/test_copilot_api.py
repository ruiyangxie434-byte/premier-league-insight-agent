import json

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes import copilot as copilot_route
from app.core.config import Settings
from app.database.seed import seed_sample_data
from app.database.session import create_schema
from app.schemas.copilot import CopilotQueryRequest
from app.services.league_copilot import run_league_copilot


def local_settings() -> Settings:
    return Settings(_env_file=None, dashscope_api_key=None)


def use_local_copilot(monkeypatch) -> None:
    monkeypatch.setattr(copilot_route, "get_settings", local_settings)


def test_copilot_capabilities_expose_six_controlled_tools(
    api_client: TestClient,
    monkeypatch,
) -> None:
    use_local_copilot(monkeypatch)
    response = api_client.get("/api/copilot/capabilities")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["default_mode"] == "local_tool_router"
    assert data["qwen_configured"] is False
    assert [item["name"] for item in data["tools"]] == [
        "get_league_table",
        "get_club_form",
        "compare_clubs",
        "compare_players",
        "find_similar_players",
        "get_match_shot_summary",
    ]


def test_copilot_reads_final_table_with_local_tool_router(
    api_client: TestClient,
    monkeypatch,
) -> None:
    use_local_copilot(monkeypatch)
    response = api_client.post(
        "/api/copilot/query",
        json={"question": "2024-25 英超积分榜前三名是谁？"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["generation"]["mode"] == "local_tool_router"
    assert data["generation"]["status"] == "not_configured"
    assert [item["tool"] for item in data["tool_calls"]] == [
        "get_league_table"
    ]
    assert data["evidence"][0]["value"] == "Liverpool · 84 分"
    assert "2025-05-25" in data["limitations"][0]


def test_copilot_uses_grounded_club_matchup_tool(
    api_client: TestClient,
    monkeypatch,
) -> None:
    use_local_copilot(monkeypatch)
    response = api_client.post(
        "/api/copilot/query",
        json={
            "question": (
                "利物浦和阿森纳的最终排名、主客场表现和近五场状态有什么差异？"
            )
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["tool"] for item in data["tool_calls"]] == [
        "compare_clubs",
    ]
    assert data["tool_calls"][0]["arguments"]["club_a"] == "liverpool"
    assert data["tool_calls"][0]["arguments"]["club_b"] == "arsenal"
    assert "Liverpool vs Arsenal" in data["headline"]
    assert "两回合总比分 4–4" in data["answer"]
    assert len(data["evidence"]) == 4
    assert any("Matchup Lab" in link["label"] for link in data["links"])
    assert any("不是下一场比赛" in item for item in data["limitations"])


def test_copilot_reuses_grounded_player_comparison_tool(
    api_client: TestClient,
    monkeypatch,
) -> None:
    use_local_copilot(monkeypatch)
    response = api_client.post(
        "/api/copilot/query",
        json={"question": "萨卡和帕尔默谁更适合承担创造任务？"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["tool"] for item in data["tool_calls"]] == [
        "compare_players"
    ]
    assert data["tool_calls"][0]["arguments"] == {
        "player_a": "bukayo-saka",
        "player_b": "cole-palmer",
        "season": "2024-25",
        "focus": "creativity",
    }
    assert "创造与组织" in data["evidence"][0]["label"]
    assert any("400 条" in item for item in data["limitations"])


def test_copilot_finds_explainable_similar_player_profiles(
    api_client: TestClient,
    monkeypatch,
) -> None:
    use_local_copilot(monkeypatch)
    response = api_client.post(
        "/api/copilot/query",
        json={"question": "找出和萨卡统计画像最相似的球员"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["tool"] for item in data["tool_calls"]] == [
        "find_similar_players"
    ]
    assert data["tool_calls"][0]["arguments"] == {
        "player": "bukayo-saka",
        "season": "2024-25",
        "minimum_minutes": 450,
        "limit": 5,
    }
    assert "Son Heung-min" in data["headline"]
    assert data["evidence"][0]["value"] == "Son Heung-min · 85/100"
    assert data["evidence"][0]["tool"] == "find_similar_players"
    assert any("首位候选双人雷达" in link["label"] for link in data["links"])
    assert any("转会建议" in item for item in data["limitations"])


def test_copilot_explains_goalkeeper_similarity_boundary(
    api_client: TestClient,
    monkeypatch,
) -> None:
    use_local_copilot(monkeypatch)
    response = api_client.post(
        "/api/copilot/query",
        json={"question": "找出和 Alisson 统计画像相似的门将"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["tool_calls"][0]["tool"] == "find_similar_players"
    assert data["evidence"][0]["value"] == "未生成排名"
    assert "当前不生成相似球员排名" in data["headline"]
    assert "门将指标" in data["answer"]


def test_copilot_requires_club_context_for_transferred_player(
    api_client: TestClient,
    monkeypatch,
) -> None:
    use_local_copilot(monkeypatch)
    ambiguous = api_client.post(
        "/api/copilot/query",
        json={"question": "比较 Trevoh Chalobah 和 Bukayo Saka 的防守表现"},
    )
    qualified = api_client.post(
        "/api/copilot/query",
        json={
            "question": (
                "比较 Chelsea 的 Trevoh Chalobah 和 Bukayo Saka 的防守表现"
            )
        },
    )

    assert ambiguous.status_code == 422
    assert qualified.status_code == 200
    comparison = next(
        item
        for item in qualified.json()["data"]["tool_calls"]
        if item["tool"] == "compare_players"
    )
    assert comparison["arguments"]["player_a"] == "trevoh-chalobah-chelsea"


def test_copilot_keeps_historical_match_separate(
    api_client: TestClient,
    monkeypatch,
) -> None:
    use_local_copilot(monkeypatch)
    response = api_client.post(
        "/api/copilot/query",
        json={"question": "2004 年 Arsenal 4-2 Liverpool 的射门和 xG 如何？"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert [item["tool"] for item in data["tool_calls"]] == [
        "get_match_shot_summary"
    ]
    assert "28 次射门" in data["answer"]
    assert data["evidence"][0]["value"] == "15 次射门 · 2.006 xG"
    assert any("不与 2024-25" in item for item in data["limitations"])


def test_copilot_rejects_questions_outside_available_tools(
    api_client: TestClient,
    monkeypatch,
) -> None:
    use_local_copilot(monkeypatch)
    response = api_client.post(
        "/api/copilot/query",
        json={"question": "帮我查询今天的实时伤病与转会新闻"},
    )

    assert response.status_code == 422
    assert response.json()["success"] is False
    assert "无法落到可用数据工具" in response.json()["message"]


def test_qwen_selects_tool_before_grounded_narrative() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    create_schema(engine)
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        calls.append(payload)
        assert request.headers["Authorization"] == "Bearer test-key"
        if "tools" in payload:
            assert len(payload["tools"]) == 6
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "call_liverpool_form",
                                        "type": "function",
                                        "function": {
                                            "name": "get_club_form",
                                            "arguments": json.dumps(
                                                {
                                                    "club": "Liverpool",
                                                    "season": "2024-25",
                                                    "recent_matches": 5,
                                                }
                                            ),
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                },
            )

        assert payload["response_format"] == {"type": "json_object"}
        grounding = json.loads(payload["messages"][1]["content"])
        assert grounding["tool_results"][0]["payload"]["final_position"] == 1
        assert grounding["tool_results"][0]["payload"]["overall"]["points"] == 84
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "headline": "利物浦的赛季状态有据可查",
                                    "answer": (
                                        "工具返回利物浦最终排名第一并得到84分；"
                                        "主客场与近五场信息均来自完整比分计算。"
                                    ),
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            },
        )

    settings = Settings(
        _env_file=None,
        dashscope_api_key="test-key",
        qwen_base_url="https://example.test/compatible-mode/v1",
        qwen_model="qwen-plus",
    )
    try:
        with Session(engine) as db:
            seed_sample_data(db)
            with httpx.Client(transport=httpx.MockTransport(handler)) as client:
                result = run_league_copilot(
                    db,
                    CopilotQueryRequest(question="利物浦最近五场状态怎么样？"),
                    settings,
                    client=client,
                )
    finally:
        engine.dispose()

    assert len(calls) == 2
    assert result.generation.mode == "qwen_tool_calling"
    assert result.generation.status == "completed"
    assert result.tool_calls[0].call_id == "call_liverpool_form"
    assert result.tool_calls[0].arguments["club"] == "liverpool"
    assert result.headline == "利物浦的赛季状态有据可查"


def test_qwen_valid_but_irrelevant_tool_falls_back_to_safe_plan() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    create_schema(engine)
    request_count = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "wrong_but_allowed_tool",
                                    "type": "function",
                                    "function": {
                                        "name": "get_match_shot_summary",
                                        "arguments": json.dumps(
                                            {"source_match_id": "3749448"}
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
        )

    settings = Settings(
        _env_file=None,
        dashscope_api_key="test-key",
        qwen_base_url="https://example.test/compatible-mode/v1",
    )
    try:
        with Session(engine) as db:
            seed_sample_data(db)
            with httpx.Client(transport=httpx.MockTransport(handler)) as client:
                result = run_league_copilot(
                    db,
                    CopilotQueryRequest(question="利物浦最近五场状态怎么样？"),
                    settings,
                    client=client,
                )
    finally:
        engine.dispose()

    assert request_count == 1
    assert result.generation.mode == "local_tool_router"
    assert result.generation.status == "fallback"
    assert [item.tool for item in result.tool_calls] == ["get_club_form"]
    assert result.tool_calls[0].arguments["club"] == "liverpool"
