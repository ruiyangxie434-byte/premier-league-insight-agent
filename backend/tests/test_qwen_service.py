import json

import httpx
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.schemas.agent import AgentAnalysisData
from app.services.qwen_service import enhance_analysis_with_qwen


def test_qwen_enhances_wording_without_changing_scores(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/api/agent/analyze",
        json={
            "question": "萨卡和帕尔默谁更适合高位逼抢？",
            "player_slugs": ["bukayo-saka", "cole-palmer"],
            "season": "2024-25",
            "focus": "pressing",
        },
    )
    local_result = AgentAnalysisData.model_validate(
        response.json()["data"]
    )
    base_result = local_result.model_copy(
        update={"steps": local_result.steps[:-1]}
    )

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        assert request.headers["Authorization"] == "Bearer test-key"
        assert payload["model"] == "qwen-plus"
        assert payload["response_format"] == {"type": "json_object"}
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "headline": (
                                        "萨卡在当前逼抢指标下略占优势"
                                    ),
                                    "summary": (
                                        "基于给定的每90分钟数据、合格球员池百分位"
                                        "和加权得分，萨卡更符合本次任务；"
                                        "这是一项样例范围内的分析判断。"
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
    with httpx.Client(
        transport=httpx.MockTransport(handler)
    ) as client:
        enhanced = enhance_analysis_with_qwen(
            base_result,
            settings,
            client=client,
        )

    assert enhanced.generation.mode == "qwen_enhanced"
    assert enhanced.generation.status == "completed"
    assert enhanced.recommendation.headline == (
        "萨卡在当前逼抢指标下略占优势"
    )
    assert (
        enhanced.recommendation.winner_slug
        == base_result.recommendation.winner_slug
    )
    assert (
        enhanced.recommendation.scores
        == base_result.recommendation.scores
    )
    assert len(enhanced.steps) == 5
