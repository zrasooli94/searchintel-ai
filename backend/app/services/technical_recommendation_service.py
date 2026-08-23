from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.technical_audit_repository import (
    TechnicalAuditRepository,
)
from app.repositories.technical_recommendation_repository import (
    TechnicalRecommendationRepository,
)
from app.services.website_service import WebsiteService


class TechnicalRecommendationService:

    RULES = {
        "NO_STATUS_CODE": {
            "title": "Investigate inaccessible page",
            "recommendation": (
                "Verify that the URL is reachable and returns a valid "
                "HTTP response to crawlers."
            ),
            "priority_score": 100,
        },
        "SERVER_ERROR": {
            "title": "Fix server error",
            "recommendation": (
                "Resolve the server-side failure so the page returns "
                "a successful HTTP response."
            ),
            "priority_score": 100,
        },
        "BROKEN_PAGE": {
            "title": "Fix broken page",
            "recommendation": (
                "Restore the page, redirect it to a relevant replacement, "
                "or remove internal links pointing to the broken URL."
            ),
            "priority_score": 95,
        },
        "MISSING_TITLE": {
            "title": "Add a descriptive title",
            "recommendation": (
                "Create a unique title that clearly describes the page "
                "topic and matches its primary search intent."
            ),
            "priority_score": 90,
        },
        "MISSING_H1": {
            "title": "Add a primary H1 heading",
            "recommendation": (
                "Add a clear H1 that communicates the page's main topic "
                "to users and search engines."
            ),
            "priority_score": 85,
        },
        "NOINDEX": {
            "title": "Review noindex directive",
            "recommendation": (
                "Confirm that this page should be excluded from search. "
                "Remove noindex if the page is intended to rank."
            ),
            "priority_score": 80,
        },
        "DUPLICATE_TITLE": {
            "title": "Create a unique page title",
            "recommendation": (
                "Differentiate this title from other pages so each URL "
                "has a clear and distinct search purpose."
            ),
            "priority_score": 70,
        },
        "MISSING_META_DESCRIPTION": {
            "title": "Add a meta description",
            "recommendation": (
                "Write a concise, useful description that summarizes "
                "the page and encourages relevant search clicks."
            ),
            "priority_score": 65,
        },
        "SHORT_TITLE": {
            "title": "Improve title depth",
            "recommendation": (
                "Expand the title so it communicates the topic more "
                "clearly. Aim for a useful descriptive title rather "
                "than filling characters artificially."
            ),
            "priority_score": 45,
        },
        "LONG_TITLE": {
            "title": "Refine the title",
            "recommendation": (
                "Make the title more concise while preserving the most "
                "important topic and search intent."
            ),
            "priority_score": 40,
        },
        "SHORT_META_DESCRIPTION": {
            "title": "Expand meta description",
            "recommendation": (
                "Add enough useful context to explain the page's value "
                "and relevance without keyword stuffing."
            ),
            "priority_score": 40,
        },
        "LONG_META_DESCRIPTION": {
            "title": "Shorten meta description",
            "recommendation": (
                "Make the description more concise and place the most "
                "important information earlier."
            ),
            "priority_score": 35,
        },
        "THIN_CONTENT": {
            "title": "Review content depth",
            "recommendation": (
                "Check whether the page fully satisfies its intended "
                "search intent. Add useful original information where "
                "the topic genuinely requires greater depth."
            ),
            "priority_score": 45,
        },
        "MISSING_CANONICAL": {
            "title": "Add or review canonical URL",
            "recommendation": (
                "Declare the preferred canonical URL where appropriate "
                "to help consolidate duplicate or similar URL signals."
            ),
            "priority_score": 40,
        },
        "MULTIPLE_H1": {
            "title": "Review heading structure",
            "recommendation": (
                "Review whether multiple H1 elements are intentional "
                "and ensure the page hierarchy remains clear."
            ),
            "priority_score": 25,
        },
        "NO_INTERNAL_OUTGOING_LINKS": {
            "title": "Improve internal linking",
            "recommendation": (
                "Add relevant internal links where useful so visitors "
                "and crawlers can discover related content."
            ),
            "priority_score": 35,
        },
        "DUPLICATE_META_DESCRIPTION": {
            "title": "Differentiate meta description",
            "recommendation": (
                "Write a page-specific description that reflects this "
                "URL's unique topic and purpose."
            ),
            "priority_score": 25,
        },
    }

    @staticmethod
    def priority_from_score(
        score: int,
    ) -> str:
        if score >= 80:
            return "high"

        if score >= 50:
            return "medium"

        return "low"

    @classmethod
    def generate(
        cls,
        db: Session,
        website_id: int,
    ) -> dict:
        WebsiteService.get(
            db,
            website_id,
        )

        audit = TechnicalAuditRepository.get_latest(
            db,
            website_id,
        )

        if audit is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Run a technical audit before "
                    "generating recommendations."
                ),
            )

        for issue in audit.issues:
            existing = (
                TechnicalRecommendationRepository.get_by_issue(
                    db,
                    audit.id,
                    issue.id,
                )
            )

            if existing:
                continue

            rule = cls.RULES.get(
                issue.code,
                {
                    "title": "Review technical SEO issue",
                    "recommendation": (
                        "Review this issue manually and determine "
                        "whether it affects crawling, indexing, "
                        "search visibility, or user experience."
                    ),
                    "priority_score": 30,
                },
            )

            score = rule["priority_score"]

            TechnicalRecommendationRepository.create(
                db=db,
                audit_id=audit.id,
                issue_id=issue.id,
                page_id=issue.page_id,
                issue_code=issue.code,
                priority=cls.priority_from_score(
                    score
                ),
                priority_score=score,
                title=rule["title"],
                recommendation=rule[
                    "recommendation"
                ],
                status="open",
            )

        db.commit()

        recommendations = (
            TechnicalRecommendationRepository.list_by_audit(
                db,
                audit.id,
            )
        )

        return {
            "audit_id": audit.id,
            "website_id": website_id,
            "recommendation_count": len(
                recommendations
            ),
            "recommendations": recommendations,
        }

    @staticmethod
    def latest(
        db: Session,
        website_id: int,
    ) -> dict:
        WebsiteService.get(
            db,
            website_id,
        )

        audit = TechnicalAuditRepository.get_latest(
            db,
            website_id,
        )

        if audit is None:
            raise HTTPException(
                status_code=404,
                detail="No technical audit found.",
            )

        recommendations = (
            TechnicalRecommendationRepository.list_by_audit(
                db,
                audit.id,
            )
        )

        return {
            "audit_id": audit.id,
            "website_id": website_id,
            "recommendation_count": len(
                recommendations
            ),
            "recommendations": recommendations,
        }
