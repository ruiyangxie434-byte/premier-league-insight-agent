from typing import Literal

from pydantic import BaseModel


class EvidenceSource(BaseModel):
    id: str
    name: str
    provider: str
    source_url: str
    license: str
    coverage: str
    snapshot_date: str
    record_count: int
    record_label: str
    powers: list[str]
    limitations: list[str]
    status: Literal["ready", "limited"]


class EvidenceCatalogData(BaseModel):
    generated_at: str
    season_focus: str
    sources: list[EvidenceSource]
    source_count: int
    ready_count: int
    total_records: int
    methodology: list[str]

