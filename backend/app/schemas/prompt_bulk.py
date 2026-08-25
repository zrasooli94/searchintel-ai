from typing import Literal

from pydantic import BaseModel, Field


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


class PromptBulkItem(BaseModel):
    text: str = Field(
        min_length=5,
    )

    category: PromptCategory

    intent: str | None = None


class PromptBulkCreate(BaseModel):
    prompts: list[PromptBulkItem] = Field(
        min_length=1,
        max_length=100,
    )


class PromptBulkResult(BaseModel):
    project_id: int

    requested: int
    created: int
    skipped_duplicates: int

    created_prompt_ids: list[int]
