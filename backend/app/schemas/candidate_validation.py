from pydantic import BaseModel, Field


class CandidateValidationRequest(BaseModel):
    model_id: int

    limit: int = Field(
        default=200,
        ge=1,
        le=250,
    )


class CandidateValidationResult(BaseModel):
    project_id: int
    model_id: int

    evaluated_count: int
    valid_count: int
    rejected_count: int
    undecided_count: int

    valid_candidates: list[str]
    rejected_candidates: list[str]
