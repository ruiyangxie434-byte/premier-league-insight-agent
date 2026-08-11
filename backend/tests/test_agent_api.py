from fastapi.testclient import TestClient


def test_agent_player_options_use_450_minute_snapshot_pool(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/agent/players?season=2024-25")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 400
    assert {
        item["slug"]
        for item in data["items"]
    } >= {"bukayo-saka", "cole-palmer"}


def test_agent_compares_players_with_trace_and_evidence(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/api/agent/analyze",
        json={
            "question": "萨卡和帕尔默，谁更适合高位逼抢体系？",
            "player_slugs": ["bukayo-saka", "cole-palmer"],
            "season": "2024-25",
            "focus": "pressing",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["task_type"] == "player_comparison"
    assert data["focus"] == "pressing"
    assert len(data["players"]) == 2
    assert len(data["steps"]) == 5
    assert all(step["status"] == "completed" for step in data["steps"])
    assert {metric["key"] for metric in data["metrics"]} >= {
        "tackles_per90",
        "interceptions_per90",
    }
    assert data["recommendation"]["winner_slug"] in {
        "bukayo-saka",
        "cole-palmer",
    }
    assert len(data["evidence"]) == 3
    assert data["generation"] == {
        "mode": "local_rules",
        "status": "not_configured",
        "provider": "local",
        "model": None,
        "note": "尚未配置千问，当前显示本地规则结论。",
    }
    assert data["context"] == {
        "parent_run_id": None,
        "follow_up_depth": 0,
        "parent_question": None,
        "parent_headline": None,
        "inherited_scope": False,
        "note": "本次为独立分析任务。",
    }


def test_agent_can_resolve_chinese_player_names(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/api/agent/analyze",
        json={
            "question": "比较萨卡和帕尔默的创造能力，给出选择理由",
            "season": "2024-25",
            "focus": "creativity",
        },
    )

    assert response.status_code == 200
    assert {
        item["slug"]
        for item in response.json()["data"]["players"]
    } == {"bukayo-saka", "cole-palmer"}


def test_agent_rejects_duplicate_players(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/agent/analyze",
        json={
            "question": "比较两名不同球员的综合表现",
            "player_slugs": ["bukayo-saka", "bukayo-saka"],
        },
    )

    assert response.status_code == 422
    assert response.json()["success"] is False


def test_agent_capabilities_do_not_expose_secrets(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/agent/capabilities")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["qwen_configured"] is False
    assert data["provider"] == "qwen"
    assert data["model"] == "qwen-plus"
    assert data["default_mode"] == "local_rules"
    assert "api_key" not in data


def test_agent_can_infer_focus_from_question(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/api/agent/analyze",
        json={
            "question": "萨卡和帕尔默谁的创造与关键传球更适合组织进攻？",
            "player_slugs": ["bukayo-saka", "cole-palmer"],
            "season": "2024-25",
            "focus": "auto",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["requested_focus"] == "auto"
    assert data["focus"] == "creativity"
    assert data["focus_label"] == "创造与组织"


def test_agent_notebook_lists_and_restores_saved_run(
    api_client: TestClient,
) -> None:
    created = api_client.post(
        "/api/agent/analyze",
        json={
            "question": "比较萨卡和帕尔默的综合表现并给出推荐",
            "player_slugs": ["bukayo-saka", "cole-palmer"],
            "season": "2024-25",
            "focus": "balanced",
        },
    )
    run_id = created.json()["data"]["run_id"]

    history = api_client.get("/api/agent/runs?limit=5")
    assert history.status_code == 200
    history_data = history.json()["data"]
    assert history_data["total"] == 1
    assert history_data["items"][0]["run_id"] == run_id
    assert history_data["items"][0]["focus"] == "balanced"
    assert len(history_data["items"][0]["players"]) == 2

    detail = api_client.get(f"/api/agent/runs/{run_id}")
    assert detail.status_code == 200
    detail_data = detail.json()["data"]
    assert detail_data["result"]["run_id"] == run_id
    assert detail_data["parent_run_id"] is None
    assert detail_data["follow_up_depth"] == 0
    assert detail_data["source_name"] == (
        "Top 5 League Football Player Stats (2017-2025)"
    )
    assert "400 条" in detail_data["source_note"]


def test_agent_follow_up_inherits_scope_and_creates_new_run(
    api_client: TestClient,
) -> None:
    created = api_client.post(
        "/api/agent/analyze",
        json={
            "question": "比较萨卡和帕尔默的综合表现并给出推荐",
            "player_slugs": ["bukayo-saka", "cole-palmer"],
            "season": "2024-25",
            "focus": "balanced",
        },
    )
    parent = created.json()["data"]

    follow_up = api_client.post(
        f"/api/agent/runs/{parent['run_id']}/follow-up",
        json={
            "question": "如果更重视创造机会，结论会发生什么变化？",
            "focus": "creativity",
        },
    )
    assert follow_up.status_code == 200
    data = follow_up.json()["data"]
    assert data["run_id"] != parent["run_id"]
    assert data["focus"] == "creativity"
    assert [item["slug"] for item in data["players"]] == [
        "bukayo-saka",
        "cole-palmer",
    ]
    assert data["context"]["parent_run_id"] == parent["run_id"]
    assert data["context"]["follow_up_depth"] == 1
    assert data["context"]["inherited_scope"] is True
    assert data["steps"][0]["tool"] == "run_memory"
    assert len(data["steps"]) == 6

    history = api_client.get("/api/agent/runs")
    assert history.json()["data"]["total"] == 2
    assert history.json()["data"]["items"][0]["run_id"] == data["run_id"]


def test_agent_notebook_returns_404_for_unknown_run(
    api_client: TestClient,
) -> None:
    detail = api_client.get("/api/agent/runs/run_missing")
    follow_up = api_client.post(
        "/api/agent/runs/run_missing/follow-up",
        json={"question": "继续分析这两名球员的创造能力"},
    )

    assert detail.status_code == 404
    assert follow_up.status_code == 404
