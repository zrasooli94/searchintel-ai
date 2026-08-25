from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.project import ProjectCreate, ProjectRead
from app.schemas.project_onboarding import (
    ProjectOnboardRequest,
    ProjectOnboardResponse,
)
from app.schemas.project_workspace import (
    ProjectWorkspaceRead,
)
from app.schemas.project_brand import (
    ProjectBrandCreate,
    ProjectBrandRead,
)
from app.services.project_brand_service import ProjectBrandService
from app.services.project_service import ProjectService
from app.services.project_onboarding_service import (
    ProjectOnboardingService,
)
from app.services.project_workspace_service import (
    ProjectWorkspaceService,
)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
):
    return ProjectService.create(
        db,
        data,
    )


@router.get(
    "",
    response_model=list[ProjectRead],
)
def list_projects(
    db: Session = Depends(get_db),
):
    return ProjectService.list_all(db)


@router.post(
    "/onboard",
    response_model=ProjectOnboardResponse,
    status_code=status.HTTP_201_CREATED,
)
def onboard_project(
    data: ProjectOnboardRequest,
    db: Session = Depends(get_db),
):
    return ProjectOnboardingService.onboard(
        db=db,
        data=data,
    )


@router.get(
    "/workspaces",
    response_model=list[ProjectWorkspaceRead],
)
def list_project_workspaces(
    db: Session = Depends(get_db),
):
    return ProjectWorkspaceService.list_all(
        db,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    return ProjectService.get(
        db,
        project_id,
    )


@router.post(
    "/{project_id}/brands",
    response_model=ProjectBrandRead,
    status_code=status.HTTP_201_CREATED,
)
def add_brand_to_project(
    project_id: int,
    data: ProjectBrandCreate,
    db: Session = Depends(get_db),
):
    return ProjectBrandService.add_brand(
        db,
        project_id,
        data,
    )


@router.get(
    "/{project_id}/brands",
    response_model=list[ProjectBrandRead],
)
def list_project_brands(
    project_id: int,
    db: Session = Depends(get_db),
):
    return ProjectBrandService.list_brands(
        db,
        project_id,
    )