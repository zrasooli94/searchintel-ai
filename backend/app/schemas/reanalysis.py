from pydantic import BaseModel


class ExperimentReanalysisRead(BaseModel):
    project_id: int
    experiment_id: int

    analysis_version: str

    total_responses: int
    stale_before: int
    skipped_current: int

    reanalyzed: int
    failed: int
    failed_run_ids: list[int]

    current_after: int
    stale_after: int
    analysis_is_current: bool
