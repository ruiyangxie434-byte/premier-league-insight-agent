from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.seed import load_player_snapshot
from app.models.agent_run import AgentRun
from app.schemas.agent import (
    AgentAnalysisData,
    AgentRunContext,
    AgentRunDetailData,
    AgentRunListData,
    AgentRunSummary,
    AgentStep,
)

PLAYER_SNAPSHOT = load_player_snapshot()
SOURCE_NAME = PLAYER_SNAPSHOT["source"]["name"]
SOURCE_URL = PLAYER_SNAPSHOT["source"]["dataset_url"]
SOURCE_NOTE = (
    "报告只使用 2024-25 固定快照中达到 450 分钟的 400 条球员—球队"
    "记录与后端计算结果，不包含伤病或实时状态。"
)
STORAGE_NOTICE = (
    "分析记录仅保存在当前项目连接的数据库中；项目尚未提供用户账户或跨设备同步。"
)


class AgentRunNotFoundError(LookupError):
    pass


def _parse_result(run: AgentRun) -> AgentAnalysisData:
    return AgentAnalysisData.model_validate(run.result_snapshot)


def save_agent_run(
    db: Session,
    result: AgentAnalysisData,
) -> AgentRun:
    player_slugs = [player.slug for player in result.players]
    run = AgentRun(
        run_id=result.run_id,
        parent_run_id=result.context.parent_run_id,
        follow_up_depth=result.context.follow_up_depth,
        question=result.question,
        season=result.season,
        requested_focus=result.requested_focus,
        resolved_focus=result.focus,
        player_a_slug=player_slugs[0],
        player_b_slug=player_slugs[1],
        winner_slug=result.recommendation.winner_slug,
        generation_mode=result.generation.mode,
        result_snapshot=result.model_dump(mode="json"),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_agent_run(db: Session, run_id: str) -> AgentRun:
    run = db.scalar(select(AgentRun).where(AgentRun.run_id == run_id))
    if run is None:
        raise AgentRunNotFoundError(f"没有找到分析记录：{run_id}")
    return run


def build_run_detail(run: AgentRun) -> AgentRunDetailData:
    return AgentRunDetailData(
        run_id=run.run_id,
        parent_run_id=run.parent_run_id,
        follow_up_depth=run.follow_up_depth,
        created_at=run.created_at,
        result=_parse_result(run),
        source_name=SOURCE_NAME,
        source_url=SOURCE_URL,
        source_note=SOURCE_NOTE,
        storage_notice=STORAGE_NOTICE,
    )


def list_agent_runs(
    db: Session,
    *,
    limit: int,
    offset: int,
) -> AgentRunListData:
    total = db.scalar(select(func.count(AgentRun.id))) or 0
    rows = db.scalars(
        select(AgentRun)
        .order_by(AgentRun.created_at.desc(), AgentRun.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    items: list[AgentRunSummary] = []
    for run in rows:
        result = _parse_result(run)
        items.append(
            AgentRunSummary(
                run_id=run.run_id,
                parent_run_id=run.parent_run_id,
                follow_up_depth=run.follow_up_depth,
                created_at=run.created_at,
                question=run.question,
                season=run.season,
                focus=result.focus,
                focus_label=result.focus_label,
                players=result.players,
                winner_slug=run.winner_slug,
                generation_mode=result.generation.mode,
            )
        )
    return AgentRunListData(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        storage_notice=STORAGE_NOTICE,
    )


def add_follow_up_context(
    result: AgentAnalysisData,
    parent: AgentRun,
) -> AgentAnalysisData:
    parent_result = _parse_result(parent)
    memory_step = AgentStep(
        index=1,
        title="读取上次分析",
        tool="run_memory",
        detail=(
            f"继承 {parent.run_id} 的两名球员与 {parent.season} 赛季口径，"
            "并使用新的问题重新计算全部指标。"
        ),
        status="completed",
    )
    renumbered_steps = [
        step.model_copy(update={"index": step.index + 1})
        for step in result.steps
    ]
    context = AgentRunContext(
        parent_run_id=parent.run_id,
        follow_up_depth=parent.follow_up_depth + 1,
        parent_question=parent.question,
        parent_headline=parent_result.recommendation.headline,
        inherited_scope=True,
        note="已继承上一次分析的球员与赛季范围，并按本次问题重新计算。",
    )
    return result.model_copy(
        update={
            "steps": [memory_step, *renumbered_steps],
            "context": context,
        }
    )
