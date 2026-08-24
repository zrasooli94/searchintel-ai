from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.brand_alias import (
    BrandAliasCreate,
    BrandAliasRead,
)
from app.services.brand_alias_service import (
    BrandAliasService,
)


router = APIRouter(
    tags=["Brands"],
)


@router.post(
    "/brands/{brand_id}/aliases",
    response_model=BrandAliasRead,
    status_code=status.HTTP_201_CREATED,
)
def create_brand_alias(
    brand_id: int,
    data: BrandAliasCreate,
    db: Session = Depends(get_db),
):
    return BrandAliasService.create(
        db,
        brand_id,
        data.alias,
    )


@router.get(
    "/brands/{brand_id}/aliases",
    response_model=list[BrandAliasRead],
)
def list_brand_aliases(
    brand_id: int,
    db: Session = Depends(get_db),
):
    return BrandAliasService.list(
        db,
        brand_id,
    )
