from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


PriorityStatus = Literal["open", "in_progress", "implemented", "ready_to_recheck", "rechecked_improved", "rechecked_unchanged", "rechecked_worsened"]


class ProjectPriorityRead(BaseModel):
    id: int
    project_id: int
    stable_key: str
    title: str
    priority: Literal["high", "medium", "low", "monitor"]
    priority_score: int
    impact: Literal["high", "medium", "low"]
    effort: Literal["high", "medium", "low"]
    confidence: Literal["high", "medium", "low"]
    status: PriorityStatus
    observed_evidence: list[str]
    interpretation: str
    recommended_action: str
    affected_prompts: list[str]
    affected_pages: list[str]
    affected_entities: list[str]
    source_modes: list[str]
    score_components: dict
    provenance: dict
    is_resolved: bool
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProjectPrioritySummary(BaseModel):
    project_id: int
    open_priorities: int
    high_priority: int
    in_progress: int
    ready_to_recheck: int
    priorities: list[ProjectPriorityRead]
    provenance_note: str


class ProjectPriorityStatusUpdate(BaseModel):
    status: PriorityStatus

