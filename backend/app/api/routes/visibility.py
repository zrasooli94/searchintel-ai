from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.reanalysis import (
    ExperimentReanalysisRead,
)
from app.schemas.visibility import (
    VisibilityAnalysisRead,
)
from app.services.experiment_reanalysis_service import (
    ExperimentReanalysisService,
)
from app.services.visibility_analysis_service import (
    VisibilityAnalysisService,
)


router = APIRouter(
    tags=["GEO Visibility"],
)


@router.post(
    "/ai-runs/{run_id}/analyze-visibility",
    response_model=VisibilityAnalysisRead,
)
def analyze_visibility(
    run_id: int,
    db: Session = Depends(get_db),
):
    return VisibilityAnalysisService.analyze(
        db,
        run_id,
    )


@router.post(
    "/projects/{project_id}/experiments/{experiment_id}/reanalyze-visibility",
    response_model=ExperimentReanalysisRead,
)
def reanalyze_experiment_visibility(
    project_id: int,
    experiment_id: int,
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    return ExperimentReanalysisService.reanalyze(
        db=db,
        project_id=project_id,
        experiment_id=experiment_id,
        force=force,
    )
