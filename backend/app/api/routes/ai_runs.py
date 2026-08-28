from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.operator import require_operator
from app.schemas.ai_run import (
    AIRunCreate,
    AIRunRead,
    AIExecutionResult,
    AIResponseCreate,
)
from app.services.ai_run_service import (
    AIRunService,
)


router = APIRouter(
    tags=["AI Runs"],
)


@router.post(
    "/projects/{project_id}/ai-runs",
    response_model=AIRunRead,
    status_code=status.HTTP_201_CREATED,
)
def create_run(
    project_id: int,
    data: AIRunCreate,
    db: Session = Depends(get_db),
):
    return AIRunService.create(
        db,
        project_id,
        data,
    )


@router.post(
    "/ai-runs/{run_id}/response",
    response_model=AIRunRead,
)
def complete_run(
    run_id: int,
    data: AIResponseCreate,
    db: Session = Depends(get_db),
):
    return AIRunService.complete(
        db,
        run_id,
        data,
    )


@router.get(
    "/projects/{project_id}/ai-runs",
    response_model=list[AIRunRead],
)
def list_runs(
    project_id: int,
    db: Session = Depends(get_db),
):
    return AIRunService.list_by_project(
        db,
        project_id,
    )



@router.post(
    "/ai-runs/{run_id}/execute",
    response_model=AIExecutionResult,
)
def execute_run(
    run_id: int,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
):
    return AIRunService.execute(
        db,
        run_id,
    )
