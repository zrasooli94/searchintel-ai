from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.technical_audit import TechnicalAudit


class TechnicalAuditRepository:

    @staticmethod
    def create(
        db: Session,
        website_id: int,
        pages_checked: int,
    ) -> TechnicalAudit:
        audit = TechnicalAudit(
            website_id=website_id,
            pages_checked=pages_checked,
            score=100,
            issue_count=0,
        )

        db.add(audit)
        db.flush()

        return audit

    @staticmethod
    def get_with_issues(
        db: Session,
        audit_id: int,
    ) -> TechnicalAudit | None:
        statement = (
            select(TechnicalAudit)
            .options(
                selectinload(TechnicalAudit.issues)
            )
            .where(TechnicalAudit.id == audit_id)
        )

        return db.scalar(statement)

    @staticmethod
    def get_latest(
        db: Session,
        website_id: int,
    ) -> TechnicalAudit | None:
        statement = (
            select(TechnicalAudit)
            .options(
                selectinload(TechnicalAudit.issues)
            )
            .where(
                TechnicalAudit.website_id == website_id
            )
            .order_by(
                TechnicalAudit.created_at.desc()
            )
            .limit(1)
        )

        return db.scalar(statement)
