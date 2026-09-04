from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.page import Page
from app.models.technical_audit import TechnicalAudit
from app.repositories.page_repository import PageRepository
from app.repositories.technical_audit_repository import (
    TechnicalAuditRepository,
)
from app.repositories.technical_issue_repository import (
    TechnicalIssueRepository,
)
from app.services.website_service import WebsiteService


class TechnicalAuditService:

    SEVERITY_WEIGHTS = {
        "high": 5,
        "medium": 3,
        "low": 1,
    }

    @staticmethod
    def add_issue(
        issues: list[dict],
        page: Page,
        code: str,
        severity: str,
        message: str,
    ) -> None:
        issues.append(
            {
                "page_id": page.id,
                "code": code,
                "severity": severity,
                "message": message,
            }
        )

    @classmethod
    def run(
        cls,
        db: Session,
        website_id: int,
    ) -> TechnicalAudit:
        WebsiteService.get(
            db,
            website_id,
        )

        pages = PageRepository.list_by_website(
            db,
            website_id,
        )

        if not pages:
            raise HTTPException(
                status_code=400,
                detail="Crawl the website before running an audit.",
            )

        audit = TechnicalAuditRepository.create(
            db=db,
            website_id=website_id,
            pages_checked=len(pages),
        )

        issues: list[dict] = []

        title_groups: dict[str, list[Page]] = defaultdict(list)
        description_groups: dict[str, list[Page]] = defaultdict(list)

        for page in pages:

            if page.status_code is None:
                cls.add_issue(
                    issues,
                    page,
                    "NO_STATUS_CODE",
                    "high",
                    "No HTTP status code was recorded.",
                )

            elif page.status_code >= 500:
                cls.add_issue(
                    issues,
                    page,
                    "SERVER_ERROR",
                    "high",
                    f"Page returned HTTP {page.status_code}.",
                )

            elif page.status_code >= 400:
                cls.add_issue(
                    issues,
                    page,
                    "BROKEN_PAGE",
                    "high",
                    f"Page returned HTTP {page.status_code}.",
                )

            title = (
                page.title.strip()
                if page.title
                else ""
            )

            if not title:
                cls.add_issue(
                    issues,
                    page,
                    "MISSING_TITLE",
                    "high",
                    "Page does not have a title tag.",
                )
            else:
                title_groups[title.lower()].append(page)

                if len(title) < 30:
                    cls.add_issue(
                        issues,
                        page,
                        "SHORT_TITLE",
                        "low",
                        f"Title is only {len(title)} characters.",
                    )

                elif len(title) > 60:
                    cls.add_issue(
                        issues,
                        page,
                        "LONG_TITLE",
                        "low",
                        f"Title is {len(title)} characters.",
                    )

            description = (
                page.meta_description.strip()
                if page.meta_description
                else ""
            )

            if not description:
                cls.add_issue(
                    issues,
                    page,
                    "MISSING_META_DESCRIPTION",
                    "medium",
                    "Page does not have a meta description.",
                )
            else:
                description_groups[
                    description.lower()
                ].append(page)

                if len(description) < 70:
                    cls.add_issue(
                        issues,
                        page,
                        "SHORT_META_DESCRIPTION",
                        "low",
                        f"Meta description is only {len(description)} characters.",
                    )

                elif len(description) > 160:
                    cls.add_issue(
                        issues,
                        page,
                        "LONG_META_DESCRIPTION",
                        "low",
                        f"Meta description is {len(description)} characters.",
                    )

            if page.h1_count == 0:
                cls.add_issue(
                    issues,
                    page,
                    "MISSING_H1",
                    "high",
                    "Page does not contain an H1 heading.",
                )

            elif page.h1_count > 1:
                cls.add_issue(
                    issues,
                    page,
                    "MULTIPLE_H1",
                    "low",
                    f"Page contains {page.h1_count} H1 headings; review whether this is intentional.",
                )

            robots = (
                page.robots_meta.lower()
                if page.robots_meta
                else ""
            )

            if "noindex" in robots:
                cls.add_issue(
                    issues,
                    page,
                    "NOINDEX",
                    "medium",
                    "Page contains a noindex directive; verify this is intentional.",
                )

            if page.word_count < 300:
                cls.add_issue(
                    issues,
                    page,
                    "THIN_CONTENT",
                    "low",
                    f"Page contains approximately {page.word_count} words.",
                )

            if not page.canonical_url:
                cls.add_issue(
                    issues,
                    page,
                    "MISSING_CANONICAL",
                    "low",
                    "Page does not declare a canonical URL.",
                )

            if page.internal_link_count == 0:
                cls.add_issue(
                    issues,
                    page,
                    "NO_INTERNAL_OUTGOING_LINKS",
                    "low",
                    "Page contains no outgoing internal links.",
                )

        for title, duplicate_pages in title_groups.items():
            if len(duplicate_pages) > 1:
                for page in duplicate_pages:
                    cls.add_issue(
                        issues,
                        page,
                        "DUPLICATE_TITLE",
                        "medium",
                        f"Title is duplicated across {len(duplicate_pages)} crawled pages.",
                    )

        for description, duplicate_pages in description_groups.items():
            if len(duplicate_pages) > 1:
                for page in duplicate_pages:
                    cls.add_issue(
                        issues,
                        page,
                        "DUPLICATE_META_DESCRIPTION",
                        "low",
                        f"Meta description is duplicated across {len(duplicate_pages)} crawled pages.",
                    )

        weighted_penalty = sum(
            cls.SEVERITY_WEIGHTS[
                issue["severity"]
            ]
            for issue in issues
        )

        average_penalty = (
            weighted_penalty / len(pages)
        )

        score = max(
            0,
            round(
                100 - average_penalty * 10
            ),
        )

        TechnicalIssueRepository.create_many(
            db=db,
            audit_id=audit.id,
            issues=issues,
        )

        audit.score = score
        audit.issue_count = len(issues)

        db.commit()

        result = TechnicalAuditRepository.get_with_issues(
            db,
            audit.id,
        )

        if result is None:
            raise RuntimeError(
                "Audit could not be reloaded."
            )

        from app.services.agency_inbox_service import AgencyInboxService
        AgencyInboxService.reconcile_safely(db)
        return result

    @staticmethod
    def latest(
        db: Session,
        website_id: int,
    ) -> TechnicalAudit:
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
                detail="No technical audit exists for this website.",
            )

        return audit
