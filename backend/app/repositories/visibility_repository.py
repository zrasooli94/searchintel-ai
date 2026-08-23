from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.brand_mention import BrandMention
from app.models.citation import Citation


class VisibilityRepository:

    @staticmethod
    def clear_response_analysis(
        db: Session,
        response_id: int,
    ) -> None:
        db.execute(
            delete(BrandMention).where(
                BrandMention.response_id == response_id
            )
        )

        db.execute(
            delete(Citation).where(
                Citation.response_id == response_id
            )
        )

        db.flush()

    @staticmethod
    def create_mention(
        db: Session,
        **data,
    ) -> BrandMention:
        mention = BrandMention(**data)

        db.add(mention)
        db.flush()

        return mention

    @staticmethod
    def create_citation(
        db: Session,
        **data,
    ) -> Citation:
        citation = Citation(**data)

        db.add(citation)
        db.flush()

        return citation

    @staticmethod
    def list_mentions(
        db: Session,
        response_id: int,
    ) -> list[BrandMention]:
        statement = (
            select(BrandMention)
            .where(
                BrandMention.response_id
                == response_id
            )
            .order_by(
                BrandMention.position
            )
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def list_citations(
        db: Session,
        response_id: int,
    ) -> list[Citation]:
        statement = (
            select(Citation)
            .where(
                Citation.response_id
                == response_id
            )
            .order_by(
                Citation.position
            )
        )

        return list(
            db.scalars(statement).all()
        )
