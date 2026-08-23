from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.brand import BrandCreate, BrandRead
from app.services.brand_service import BrandService


router = APIRouter(
    prefix="/brands",
    tags=["Brands"],
)


@router.post(
    "",
    response_model=BrandRead,
    status_code=status.HTTP_201_CREATED,
)
def create_brand(
    data: BrandCreate,
    db: Session = Depends(get_db),
):
    return BrandService.create(
        db,
        data,
    )


@router.get(
    "",
    response_model=list[BrandRead],
)
def list_brands(
    db: Session = Depends(get_db),
):
    return BrandService.list_all(db)


@router.get(
    "/{brand_id}",
    response_model=BrandRead,
)
def get_brand(
    brand_id: int,
    db: Session = Depends(get_db),
):
    return BrandService.get(
        db,
        brand_id,
    )