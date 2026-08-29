from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.page_repository import (
    PageRepository,
)
from app.repositories.project_brand_repository import (
    ProjectBrandRepository,
)
from app.repositories.technical_audit_repository import (
    TechnicalAuditRepository,
)
from app.repositories.technical_recommendation_repository import (
    TechnicalRecommendationRepository,
)
from app.repositories.website_repository import (
    WebsiteRepository,
)


class TechnicalSEOSummaryService:

    CHECK_GROUPS = [
        {
            "key": "http_status",
            "label": "HTTP status",
            "codes": {
                "NO_STATUS_CODE",
                "SERVER_ERROR",
                "BROKEN_PAGE",
            },
        },
        {
            "key": "titles",
            "label": "Page titles",
            "codes": {
                "MISSING_TITLE",
                "SHORT_TITLE",
                "LONG_TITLE",
                "DUPLICATE_TITLE",
            },
        },
        {
            "key": "meta_descriptions",
            "label": "Meta descriptions",
            "codes": {
                "MISSING_META_DESCRIPTION",
                "SHORT_META_DESCRIPTION",
                "LONG_META_DESCRIPTION",
                "DUPLICATE_META_DESCRIPTION",
            },
        },
        {
            "key": "h1",
            "label": "H1 structure",
            "codes": {
                "MISSING_H1",
                "MULTIPLE_H1",
            },
        },
        {
            "key": "indexability",
            "label": "Indexability",
            "codes": {
                "NOINDEX",
            },
        },
        {
            "key": "canonical",
            "label": "Canonical URLs",
            "codes": {
                "MISSING_CANONICAL",
            },
        },
        {
            "key": "content",
            "label": "Content depth",
            "codes": {
                "THIN_CONTENT",
            },
        },
        {
            "key": "internal_links",
            "label": "Internal linking",
            "codes": {
                "NO_INTERNAL_OUTGOING_LINKS",
            },
        },
    ]

    @staticmethod
    def _page_path(
        url: str,
    ) -> str:

        parsed = urlparse(url)

        path = parsed.path or "/"

        if parsed.query:
            path += f"?{parsed.query}"

        return path

    @classmethod
    def build(
        cls,
        db: Session,
        project_id: int,
    ) -> dict:

        project_brands = (
            ProjectBrandRepository.list_brand_roles(
                db,
                project_id,
            )
        )

        target_rows = [
            (brand, role)
            for brand, role
            in project_brands
            if role == "target"
        ]

        if not target_rows:
            raise HTTPException(
                status_code=400,
                detail="Project has no target brand.",
            )

        target_brand = target_rows[0][0]

        websites = (
            WebsiteRepository.list_by_brand(
                db,
                target_brand.id,
            )
        )

        if not websites:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Target brand has no registered "
                    "website."
                ),
            )

        primary_websites = [
            website
            for website in websites
            if website.is_primary
        ]

        website = (
            primary_websites[0]
            if primary_websites
            else websites[0]
        )

        pages = (
            PageRepository.list_by_website(
                db,
                website.id,
            )
        )

        audit = (
            TechnicalAuditRepository.get_latest(
                db,
                website.id,
            )
        )

        if audit is None:
            crawl = website.last_crawl_summary or {}
            blocked_count = int(
                crawl.get(
                    "pages_blocked_by_robots",
                    0,
                )
                or 0
            )
            if blocked_count > 0:
                return {
                    "project_id": project_id,
                    "measurement_state": "limited",
                    "measurement_reason": (
                        "SearchIntelBot was blocked by the "
                        "website's robots policy during the "
                        "latest bounded crawl attempt."
                    ),
                    "limitation_note": (
                        "This limitation applies only to "
                        "SearchIntel's crawler and does not "
                        "imply that Google or another crawler "
                        "cannot access the site."
                    ),
                    "coverage_state": "unavailable",
                    "coverage_label": "LIMITED",
                    "coverage_reason": (
                        "No usable pages were available for "
                        "the latest bounded technical audit."
                    ),
                    "website": {
                        "id": website.id,
                        "brand_id": target_brand.id,
                        "brand": target_brand.name,
                        "domain": website.domain,
                        "base_url": website.base_url,
                        "is_primary": website.is_primary,
                    },
                    "audit": None,
                    "crawled_pages": 0,
                    "successful_pages": 0,
                    "failed_pages": 0,
                    "total_words": 0,
                    "average_word_count": 0.0,
                    "pages": [],
                    "checks": [],
                    "issues": [],
                    "recommendation_count": 0,
                    "recommendations": [],
                }
            raise HTTPException(
                status_code=404,
                detail=(
                    "No technical audit exists for "
                    "the target website."
                ),
            )

        recommendations = (
            TechnicalRecommendationRepository
            .list_by_audit(
                db,
                audit.id,
            )
        )

        issue_codes = [
            issue.code
            for issue in audit.issues
        ]

        checks = []

        for group in cls.CHECK_GROUPS:

            issue_count = sum(
                1
                for code in issue_codes
                if code in group["codes"]
            )

            checks.append(
                {
                    "key":
                        group["key"],

                    "label":
                        group["label"],

                    "status":
                        (
                            "passed"
                            if issue_count == 0
                            else "issue"
                        ),

                    "issue_count":
                        issue_count,
                }
            )

        high_issues = sum(
            1
            for issue in audit.issues
            if issue.severity == "high"
        )

        medium_issues = sum(
            1
            for issue in audit.issues
            if issue.severity == "medium"
        )

        low_issues = sum(
            1
            for issue in audit.issues
            if issue.severity == "low"
        )

        successful_pages = sum(
            1
            for page in pages
            if (
                page.status_code is not None
                and 200 <= page.status_code < 400
            )
        )

        failed_pages = (
            len(pages)
            - successful_pages
        )

        total_words = sum(
            page.word_count
            for page in pages
        )

        average_word_count = (
            round(
                total_words / len(pages),
                2,
            )
            if pages
            else 0.0
        )

        limited_sample = audit.pages_checked <= 1
        coverage_state = (
            "limited_sample"
            if limited_sample
            else "bounded_sample"
        )
        coverage_label = (
            "LIMITED SAMPLE"
            if limited_sample
            else "BOUNDED SAMPLE"
        )
        coverage_reason = (
            "SearchIntel's bounded crawl currently contains "
            "one usable page. Technical findings apply to "
            "the crawled sample and may not represent the "
            "broader site."
            if limited_sample
            else (
                "Technical findings reflect the "
                f"{audit.pages_checked} pages analyzed in "
                "SearchIntel's latest bounded crawl."
            )
        )
        page_urls = {
            page.id: page.url
            for page in pages
        }

        return {
            "project_id":
                project_id,

            "measurement_state":
                "ready",

            "measurement_reason":
                None,

            "limitation_note":
                None,

            "coverage_state":
                coverage_state,

            "coverage_label":
                coverage_label,

            "coverage_reason":
                coverage_reason,

            "website": {
                "id":
                    website.id,

                "brand_id":
                    target_brand.id,

                "brand":
                    target_brand.name,

                "domain":
                    website.domain,

                "base_url":
                    website.base_url,

                "is_primary":
                    website.is_primary,
            },

            "audit": {
                "id":
                    audit.id,

                "score":
                    audit.score,

                "pages_checked":
                    audit.pages_checked,

                "issue_count":
                    audit.issue_count,

                "high_issues":
                    high_issues,

                "medium_issues":
                    medium_issues,

                "low_issues":
                    low_issues,

                "created_at":
                    audit.created_at,
            },

            "crawled_pages":
                len(pages),

            "successful_pages":
                successful_pages,

            "failed_pages":
                failed_pages,

            "total_words":
                total_words,

            "average_word_count":
                average_word_count,

            "pages": [
                {
                    "id":
                        page.id,

                    "url":
                        page.url,

                    "path":
                        cls._page_path(
                            page.url
                        ),

                    "status_code":
                        page.status_code,

                    "title":
                        page.title,

                    "meta_description":
                        page.meta_description,

                    "h1":
                        page.h1,

                    "canonical_url":
                        page.canonical_url,

                    "robots_meta":
                        page.robots_meta,

                    "word_count":
                        page.word_count,

                    "internal_link_count":
                        page.internal_link_count,

                    "external_link_count":
                        page.external_link_count,

                    "last_crawled_at":
                        page.last_crawled_at,
                }
                for page in pages
            ],

            "checks":
                checks,

            "issues": [
                {
                    "id": issue.id,
                    "page_id": issue.page_id,
                    "page_url": page_urls.get(
                        issue.page_id,
                        website.base_url,
                    ),
                    "code": issue.code,
                    "severity": issue.severity,
                    "message": issue.message,
                }
                for issue in audit.issues
            ],

            "recommendation_count":
                len(recommendations),

            "recommendations": [
                {
                    "id":
                        recommendation.id,

                    "page_id":
                        recommendation.page_id,

                    "issue_code":
                        recommendation.issue_code,

                    "priority":
                        recommendation.priority,

                    "priority_score":
                        recommendation.priority_score,

                    "title":
                        recommendation.title,

                    "recommendation":
                        recommendation.recommendation,

                    "status":
                        recommendation.status,
                }
                for recommendation
                in recommendations
            ],
        }
