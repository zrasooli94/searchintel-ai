from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client_report import ClientReport


class ClientReportRepository:
    @staticmethod
    def list_by_project(db: Session, project_id: int) -> list[ClientReport]:
        return list(db.scalars(select(ClientReport).where(ClientReport.project_id == project_id).order_by(ClientReport.id.desc())).all())

    @staticmethod
    def get(db: Session, project_id: int, report_id: int) -> ClientReport | None:
        return db.scalar(select(ClientReport).where(ClientReport.project_id == project_id, ClientReport.id == report_id))

    @staticmethod
    def by_token_hash(db: Session, token_hash: str) -> ClientReport | None:
        return db.scalar(select(ClientReport).where(ClientReport.share_token_hash == token_hash))
