from sqlalchemy.orm import Session

from app.models.technical_issue import TechnicalIssue


class TechnicalIssueRepository:

    @staticmethod
    def create_many(
        db: Session,
        audit_id: int,
        issues: list[dict],
    ) -> list[TechnicalIssue]:
        records = [
            TechnicalIssue(
                audit_id=audit_id,
                **issue,
            )
            for issue in issues
        ]

        db.add_all(records)
        db.flush()

        return records
