from typing import Literal

from pydantic import BaseModel, Field


CopilotToolName = Literal[
    "get_league_table",
    "get_club_form",
    "compare_players",
    "get_match_shot_summary",
]
CopilotMode = Literal["local_tool_router", "qwen_tool_calling"]
CopilotStatus = Literal["completed", "not_configured", "fallback"]


class CopilotQueryRequest(BaseModel):
    question: str = Field(min_length=6, max_length=500)
    season: str = Field(default="2024-25", pattern=r"^\d{4}-\d{2}$")


class CopilotToolCapability(BaseModel):
    name: CopilotToolName
    label: str
    description: str
    data_scope: str


class CopilotCapabilitiesData(BaseModel):
    qwen_configured: bool
    model: str
    default_mode: CopilotMode
    tools: list[CopilotToolCapability]
    message: str


class CopilotSource(BaseModel):
    name: str
    url: str
    license_name: str | None = None
    license_url: str | None = None
    data_scope: str


class CopilotEvidence(BaseModel):
    label: str
    value: str
    detail: str
    tool: CopilotToolName


class CopilotToolTrace(BaseModel):
    index: int
    call_id: str
    tool: CopilotToolName
    label: str
    arguments: dict[str, str | int | float | bool | None]
    summary: str
    evidence: list[CopilotEvidence]
    source: CopilotSource
    status: Literal["completed"] = "completed"


class CopilotGeneration(BaseModel):
    mode: CopilotMode
    status: CopilotStatus
    provider: Literal["local", "qwen"]
    model: str | None
    note: str


class CopilotLink(BaseModel):
    label: str
    href: str


class CopilotAnswerData(BaseModel):
    run_id: str
    question: str
    season: str
    headline: str
    answer: str
    generation: CopilotGeneration
    tool_calls: list[CopilotToolTrace]
    evidence: list[CopilotEvidence]
    links: list[CopilotLink]
    limitations: list[str]
    suggestions: list[str]
    scope_notice: str
