from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.technical_audit import TechnicalAuditRead
from app.services.technical_audit_service import (
    TechnicalAuditService,
)


router = APIRouter(
    tags=["Technical SEO"],
)


@router.post(
    "/websites/{website_id}/technical-audit",
    response_model=TechnicalAuditRead,
)
def run_technical_audit(
    website_id: int,
    db: Session = Depends(get_db),
):
    return TechnicalAuditService.run(
        db,
        website_id,
    )


@router.get(
    "/websites/{website_id}/technical-audits/latest",
    response_model=TechnicalAuditRead,
)
def get_latest_technical_audit(
    website_id: int,
    db: Session = Depends(get_db),
):
    return TechnicalAuditService.latest(
        db,
        website_id,
    )
