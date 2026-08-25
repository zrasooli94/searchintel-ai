from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.prompt import PromptCreate, PromptRead
from app.schemas.prompt_bulk import (
    PromptBulkCreate,
    PromptBulkResult,
)
from app.services.prompt_service import PromptService
from app.services.prompt_bulk_service import (
    PromptBulkService,
)


router = APIRouter(
    tags=["GEO Prompts"],
)


@router.post(
    "/projects/{project_id}/prompts/bulk",
    response_model=PromptBulkResult,
    status_code=status.HTTP_201_CREATED,
)
def create_prompts_bulk(
    project_id: int,
    data: PromptBulkCreate,
    db: Session = Depends(get_db),
):
    return PromptBulkService.create(
        db=db,
        project_id=project_id,
        data=data,
    )


@router.post(
    "/projects/{project_id}/prompts",
    response_model=PromptRead,
    status_code=status.HTTP_201_CREATED,
)
def create_prompt(
    project_id: int,
    data: PromptCreate,
    db: Session = Depends(get_db),
):
    return PromptService.create(
        db,
        project_id,
        data,
    )


@router.get(
    "/projects/{project_id}/prompts",
    response_model=list[PromptRead],
)
def list_prompts(
    project_id: int,
    db: Session = Depends(get_db),
):
    return PromptService.list_by_project(
        db,
        project_id,
    )
