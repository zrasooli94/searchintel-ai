from pydantic import BaseModel, Field


class PromptActiveSetUpdate(BaseModel):
    prompt_ids: list[int] = Field(
        min_length=1,
        max_length=100,
    )


class PromptActiveSetResult(BaseModel):
    project_id: int

    total_prompts: int
    active_prompts: int
    inactive_prompts: int

    active_prompt_ids: list[int]
