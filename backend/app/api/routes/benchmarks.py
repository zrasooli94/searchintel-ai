from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    status,
)
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.operator import require_operator
from app.schemas.benchmark import (
    BenchmarkJobItemRead,
    BenchmarkJobRead,
    BenchmarkStartRequest,
)
from app.services.benchmark_service import (
    BenchmarkService,
)


router = APIRouter(
    tags=["GEO Benchmarks"],
)


@router.get(
    "/projects/{project_id}/benchmark-jobs",
    response_model=list[BenchmarkJobRead],
)
def list_benchmark_jobs(
    project_id: int,
    db: Session = Depends(get_db),
):
    return BenchmarkService.list_for_project(
        db,
        project_id,
    )


@router.post(
    "/projects/{project_id}/benchmark-jobs",
    response_model=BenchmarkJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_benchmark(
    project_id: int,
    data: BenchmarkStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
):
    job = BenchmarkService.create(
        db=db,
        project_id=project_id,
        model_id=data.model_id,
        experiment_id=data.experiment_id,
        benchmark_mode=data.benchmark_mode,
        source_benchmark_job_id=(
            data.source_benchmark_job_id
        ),
        prompt_source_benchmark_job_id=(
            data.prompt_source_benchmark_job_id
        ),
    )

    background_tasks.add_task(
        BenchmarkService.run_job,
        job["id"],
    )

    return job


@router.get(
    "/benchmark-jobs/{job_id}",
    response_model=BenchmarkJobRead,
)
def benchmark_status(
    job_id: int,
    db: Session = Depends(get_db),
):
    return BenchmarkService.status(
        db,
        job_id,
    )


@router.get(
    "/benchmark-jobs/{job_id}/items",
    response_model=list[BenchmarkJobItemRead],
)
def benchmark_items(
    job_id: int,
    db: Session = Depends(get_db),
):
    return BenchmarkService.items(
        db,
        job_id,
    )
