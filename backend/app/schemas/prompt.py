from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


PromptCategory = Literal[
    "informational",
    "navigational",
    "commercial",
    "transactional",
    "comparison",
    "recommendation",
    "problem_solution",
    "brand",
]


class PromptCreate(BaseModel):
    text: str
    category: PromptCategory
    intent: str | None = None


class PromptRead(BaseModel):
    id: int
    project_id: int
    text: str
    category: str
    intent: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
