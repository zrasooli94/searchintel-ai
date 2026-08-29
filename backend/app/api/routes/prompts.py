from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.operator import require_operator
from app.schemas.prompt import PromptCreate, PromptRead
from app.schemas.prompt_update import (
    PromptUpdateRequest,
)
from app.schemas.prompt_active_set import (
    PromptActiveSetResult,
    PromptActiveSetUpdate,
)
from app.schemas.prompt_bulk import (
    PromptBulkCreate,
    PromptBulkResult,
)
from app.schemas.starter_prompt_generation import (
    PromptProposalApplyRequest,
    PromptProposalApplyResult,
    StarterPromptGenerateRequest,
    StarterPromptGenerationResult,
)
from app.services.prompt_service import PromptService
from app.services.prompt_update_service import (
    PromptUpdateService,
)
from app.services.prompt_active_set_service import (
    PromptActiveSetService,
)
from app.services.prompt_bulk_service import (
    PromptBulkService,
)
from app.services.starter_prompt_generation_service import (
    StarterPromptGenerationService,
)
from app.services.prompt_proposal_apply_service import PromptProposalApplyService


router = APIRouter(
    tags=["GEO Prompts"],
)


@router.put(
    "/projects/{project_id}/prompts/active-set",
    response_model=PromptActiveSetResult,
)
def update_prompt_active_set(
    project_id: int,
    data: PromptActiveSetUpdate,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
):
    return PromptActiveSetService.update(
        db=db,
        project_id=project_id,
        prompt_ids=data.prompt_ids,
    )


@router.post(
    "/projects/{project_id}/prompts/starter-generate",
    response_model=StarterPromptGenerationResult,
)
def generate_starter_prompts(
    project_id: int,
    data: StarterPromptGenerateRequest,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
):
    return StarterPromptGenerationService.generate(
        db=db,
        project_id=project_id,
        count=data.count,
        model_id=data.model_id,
        measurement_scope=data.measurement_scope,
        focus_label=data.focus_label,
    )


@router.get(
    "/projects/{project_id}/prompts/starter-proposal",
    response_model=StarterPromptGenerationResult | None,
)
def get_starter_prompt_proposal(project_id: int, db: Session = Depends(get_db)):
    return StarterPromptGenerationService.latest(db, project_id)


@router.post(
    "/projects/{project_id}/prompts/starter-proposals/{proposal_id}/apply",
    response_model=PromptProposalApplyResult,
)
def apply_starter_prompt_proposal(
    project_id: int,
    proposal_id: int,
    data: PromptProposalApplyRequest,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
):
    return PromptProposalApplyService.apply(db, project_id, proposal_id, data.prompts)


@router.post(
    "/projects/{project_id}/prompts/bulk",
    response_model=PromptBulkResult,
    status_code=status.HTTP_201_CREATED,
)
def create_prompts_bulk(
    project_id: int,
    data: PromptBulkCreate,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
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
    _operator: None = Depends(require_operator),
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


@router.put(
    "/projects/{project_id}/prompts/{prompt_id}",
    response_model=PromptRead,
)
def update_project_prompt(
    project_id: int,
    prompt_id: int,
    data: PromptUpdateRequest,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
):
    return PromptUpdateService.update(
        db=db,
        project_id=project_id,
        prompt_id=prompt_id,
        data=data,
    )
