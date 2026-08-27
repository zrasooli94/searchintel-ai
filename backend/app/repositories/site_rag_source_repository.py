from sqlalchemy import (
    delete,
    select,
)
from sqlalchemy.orm import Session

from app.models.site_rag_source import (
    SiteRAGSource,
)


class SiteRAGSourceRepository:

    @staticmethod
    def clear_by_response(
        db: Session,
        response_id: int,
    ) -> None:
        db.execute(
            delete(SiteRAGSource).where(
                SiteRAGSource.response_id
                == response_id
            )
        )

        db.flush()

    @staticmethod
    def create(
        db: Session,
        **data,
    ) -> SiteRAGSource:
        source = SiteRAGSource(
            **data
        )

        db.add(source)
        db.flush()

        return source

    @staticmethod
    def list_by_response(
        db: Session,
        response_id: int,
    ) -> list[SiteRAGSource]:
        statement = (
            select(SiteRAGSource)
            .where(
                SiteRAGSource.response_id
                == response_id
            )
            .order_by(
                SiteRAGSource.rank
            )
        )

        return list(
            db.scalars(statement).all()
        )
