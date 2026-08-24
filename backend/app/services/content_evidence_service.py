import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.page import Page
from app.models.website import Website


class ContentEvidenceService:

    STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "best",
        "can",
        "for",
        "how",
        "in",
        "is",
        "of",
        "on",
        "the",
        "to",
        "what",
        "which",
        "with",
    }

    @classmethod
    def tokens(
        cls,
        value: str,
    ) -> set[str]:

        words = re.findall(
            r"[a-z0-9]+",
            value.lower(),
        )

        return {
            word
            for word in words
            if (
                len(word) >= 3
                and word not in cls.STOPWORDS
            )
        }

    @classmethod
    def relevance_score(
        cls,
        prompt: str,
        page: Page,
    ) -> float:

        query = cls.tokens(prompt)

        if not query:
            return 0.0

        title = cls.tokens(
            page.title or ""
        )

        h1 = cls.tokens(
            page.h1 or ""
        )

        content = cls.tokens(
            (page.content_text or "")[:10000]
        )

        score = (
            len(query & title) * 5
            + len(query & h1) * 4
            + len(query & content)
        )

        return float(score)

    @classmethod
    def relevant_pages(
        cls,
        db: Session,
        brand_id: int,
        prompt: str,
        limit: int = 5,
    ) -> list[dict]:

        statement = (
            select(Page)
            .join(
                Website,
                Page.website_id == Website.id,
            )
            .where(
                Website.brand_id == brand_id
            )
        )

        pages = list(
            db.scalars(statement).all()
        )

        ranked = []

        for page in pages:
            score = cls.relevance_score(
                prompt,
                page,
            )

            ranked.append(
                {
                    "page": page,
                    "score": score,
                }
            )

        ranked.sort(
            key=lambda item: (
                -item["score"],
                item["page"].id,
            )
        )

        evidence = []

        for item in ranked[:limit]:
            page = item["page"]

            evidence.append(
                {
                    "page_id": page.id,
                    "url": page.url,
                    "title": page.title,
                    "h1": page.h1,
                    "meta_description":
                        page.meta_description,
                    "word_count":
                        page.word_count,
                    "relevance_score":
                        item["score"],
                    "content_excerpt":
                        (
                            page.content_text
                            or ""
                        )[:3500],
                }
            )

        return evidence
