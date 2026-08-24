from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
)
from app.schemas.geo_experiment import (
    AdoptRunsResult,
    ExperimentComparison,
    GeoExperimentCreate,
    GeoExperimentRead,
)
from app.schemas.visibility_metrics import (
    AIVisibilityMetrics,
)
from app.services.experiment_comparison_service import (
    ExperimentComparisonService,
)
from app.services.geo_experiment_service import (
    GeoExperimentService,
)
from app.services.visibility_metrics_service import (
    VisibilityMetricsService,
)


router = APIRouter(
    tags=["GEO Experiments"],
)


@router.post(
    "/projects/{project_id}/geo-experiments",
    response_model=GeoExperimentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_experiment(
    project_id: int,
    data: GeoExperimentCreate,
    db: Session = Depends(get_db),
):
    return GeoExperimentService.create(
        db=db,
        project_id=project_id,
        name=data.name,
        phase=data.phase,
        description=data.description,
    )


@router.get(
    "/projects/{project_id}/geo-experiments",
    response_model=list[GeoExperimentRead],
)
def list_experiments(
    project_id: int,
    db: Session = Depends(get_db),
):
    return GeoExperimentService.list(
        db,
        project_id,
    )


@router.post(
    "/geo-experiments/{experiment_id}/adopt-unassigned-runs",
    response_model=AdoptRunsResult,
)
def adopt_unassigned_runs(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    return (
        GeoExperimentService
        .adopt_unassigned_runs(
            db,
            experiment_id,
        )
    )


@router.post(
    "/geo-experiments/{experiment_id}/visibility-metrics",
    response_model=AIVisibilityMetrics,
)
def experiment_metrics(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    record = GeoExperimentRepository.get(
        db,
        experiment_id,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found.",
        )

    return VisibilityMetricsService.calculate(
        db=db,
        project_id=record.project_id,
        experiment_id=experiment_id,
    )



@router.get(
    "/projects/{project_id}/geo-experiments/compare",
    response_model=ExperimentComparison,
)
def compare_experiments(
    project_id: int,
    baseline_id: int,
    comparison_id: int,
    db: Session = Depends(get_db),
):
    return ExperimentComparisonService.compare(
        db=db,
        project_id=project_id,
        baseline_id=baseline_id,
        comparison_id=comparison_id,
    )
