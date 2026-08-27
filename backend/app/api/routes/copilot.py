from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.copilot import (
    CopilotAnswerData,
    CopilotCapabilitiesData,
    CopilotQueryRequest,
)
from app.services.copilot_tools import TOOL_CAPABILITIES, CopilotToolError
from app.services.league_copilot import CopilotInputError, run_league_copilot

router = APIRouter(prefix="/copilot", tags=["league-copilot"])


@router.get(
    "/capabilities",
    response_model=ApiResponse[CopilotCapabilitiesData],
)
def get_copilot_capabilities() -> ApiResponse[CopilotCapabilitiesData]:
    settings = get_settings()
    configured = settings.qwen_configured
    return ApiResponse(
        message="League Copilot 能力状态获取成功",
        data=CopilotCapabilitiesData(
            qwen_configured=configured,
            model=settings.qwen_model,
            default_mode=(
                "qwen_tool_calling" if configured else "local_tool_router"
            ),
            tools=TOOL_CAPABILITIES,
            message=(
                "千问将从九个受控数据工具中规划调用，所有参数由后端校验。"
                if configured
                else "未配置千问，当前由本地路由选择同一组真实数据工具。"
            ),
        ),
    )


@router.post("/query", response_model=ApiResponse[CopilotAnswerData])
def query_league_copilot(
    payload: CopilotQueryRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[CopilotAnswerData]:
    try:
        result = run_league_copilot(
            db,
            payload,
            get_settings(),
        )
    except (CopilotInputError, CopilotToolError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ApiResponse(
        message="League Copilot 已完成受控工具查询",
        data=result,
    )
