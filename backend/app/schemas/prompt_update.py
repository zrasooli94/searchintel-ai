from pydantic import (
    BaseModel,
    Field,
)

from app.schemas.prompt import (
    PromptCategory,
)


class PromptUpdateRequest(BaseModel):
    text: str = Field(
        min_length=5,
    )

    category: PromptCategory

    intent: str | None = None
