from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.ai_engine import (
    AIEngineCreate,
    AIEngineRead,
)
from app.schemas.ai_model import (
    AIModelCreate,
    AIModelRead,
)
from app.services.ai_engine_service import (
    AIEngineService,
)
from app.services.ai_model_service import (
    AIModelService,
)


router = APIRouter(
    tags=["AI Engines"],
)


@router.post(
    "/ai-engines",
    response_model=AIEngineRead,
    status_code=status.HTTP_201_CREATED,
)
def create_engine(
    data: AIEngineCreate,
    db: Session = Depends(get_db),
):
    return AIEngineService.create(
        db,
        data,
    )


@router.get(
    "/ai-engines",
    response_model=list[AIEngineRead],
)
def list_engines(
    db: Session = Depends(get_db),
):
    return AIEngineService.list_all(
        db
    )


@router.post(
    "/ai-engines/{engine_id}/models",
    response_model=AIModelRead,
    status_code=status.HTTP_201_CREATED,
)
def create_model(
    engine_id: int,
    data: AIModelCreate,
    db: Session = Depends(get_db),
):
    return AIModelService.create(
        db,
        engine_id,
        data,
    )


@router.get(
    "/ai-engines/{engine_id}/models",
    response_model=list[AIModelRead],
)
def list_models(
    engine_id: int,
    db: Session = Depends(get_db),
):
    return AIModelService.list_by_engine(
        db,
        engine_id,
    )
