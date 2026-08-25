from pydantic import (
    BaseModel,
    Field,
)


class StarterPromptGenerateRequest(BaseModel):
    count: int = Field(
        default=16,
        ge=8,
        le=20,
    )

    model_id: int | None = None


class StarterPromptSuggestion(BaseModel):
    text: str
    category: str
    rationale: str | None = None


class StarterPromptGenerationResult(BaseModel):
    project_id: int

    model_id: int
    model_name: str
    provider_model_id: str

    target_brand: str

    website_pages_used: int
    competitors_used: list[str]
    existing_prompts_considered: int

    requested_count: int
    generated_count: int

    prompts: list[
        StarterPromptSuggestion
    ]
