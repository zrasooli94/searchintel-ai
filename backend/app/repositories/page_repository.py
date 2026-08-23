from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.page import Page


class PageRepository:

    @staticmethod
    def get_by_url(
        db: Session,
        website_id: int,
        url: str,
    ) -> Page | None:
        statement = select(Page).where(
            Page.website_id == website_id,
            Page.url == url,
        )

        return db.scalar(statement)

    @staticmethod
    def upsert(
        db: Session,
        website_id: int,
        url: str,
        data: dict,
    ) -> Page:
        page = PageRepository.get_by_url(
            db,
            website_id,
            url,
        )

        if page is None:
            page = Page(
                website_id=website_id,
                url=url,
            )

            db.add(page)

        for key, value in data.items():
            setattr(page, key, value)

        db.flush()

        return page

    @staticmethod
    def list_by_website(
        db: Session,
        website_id: int,
    ) -> list[Page]:
        statement = (
            select(Page)
            .where(Page.website_id == website_id)
            .order_by(Page.id)
        )

        return list(
            db.scalars(statement).all()
        )