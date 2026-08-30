from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.operator import require_operator
from app.db.deps import get_db
from app.schemas.project_priority import ProjectPriorityRead, ProjectPriorityStatusUpdate, ProjectPrioritySummary
from app.services.project_priority_service import ProjectPriorityService


router = APIRouter(tags=["Priority Center"])


@router.get("/projects/{project_id}/priorities", response_model=ProjectPrioritySummary)
def get_priorities(project_id: int, db: Session = Depends(get_db)):
    return ProjectPriorityService.summary(db, project_id)


@router.post("/projects/{project_id}/priorities/refresh", response_model=ProjectPrioritySummary)
def refresh_priorities(project_id: int, db: Session = Depends(get_db), _operator: None = Depends(require_operator)):
    return ProjectPriorityService.refresh(db, project_id)


@router.patch("/projects/{project_id}/priorities/{priority_id}", response_model=ProjectPriorityRead)
def update_priority_status(
    project_id: int,
    priority_id: int,
    data: ProjectPriorityStatusUpdate,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
):
    return ProjectPriorityService.update_status(db, project_id, priority_id, data.status)

