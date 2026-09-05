from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.services.agency_portfolio_service import AgencyPortfolioService


router = APIRouter(prefix="/clients", tags=["Agency Portfolio"])


@router.get("")
def list_clients(db: Session = Depends(get_db)):
    return AgencyPortfolioService.build(db)
