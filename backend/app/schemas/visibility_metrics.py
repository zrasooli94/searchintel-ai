from pydantic import BaseModel


class ShareOfVoiceItem(BaseModel):
    brand_id: int | None
    name: str
    mention_count: int
    share_of_voice: float


class AIVisibilityMetrics(BaseModel):
    project_id: int
    experiment_id: int | None = None
    target_brand_id: int
    target_brand: str

    analyzed_runs: int
    analyzed_prompts: int

    target_mention_count: int

    mention_rate: float
    prompt_coverage: float
    citation_rate: float

    average_mention_position: float | None
    target_share_of_voice: float

    position_quality: float
    visibility_score_v1: float

    share_of_voice: list[ShareOfVoiceItem]
