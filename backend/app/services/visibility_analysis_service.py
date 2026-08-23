import re

from datetime import datetime, timezone

from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.ai_run_repository import (
    AIRunRepository,
)
from app.repositories.project_brand_repository import (
    ProjectBrandRepository,
)
from app.repositories.visibility_repository import (
    VisibilityRepository,
)
from app.repositories.website_repository import (
    WebsiteRepository,
)


class VisibilityAnalysisService:

    CANDIDATE_STOPWORDS = {
        "platform",
        "best for",
        "key strengths",
        "main considerations",
        "interoperability",
        "commercial operations",
        "energy management",
        "reliability and support",
        "security and compliance",
        "practical recommendations",
    }

    PROTOCOL_PREFIXES = (
        "ocpp",
        "ocpi",
        "iso ",
        "http",
        "api",
        "sso",
        "pci",
        "gdpr",
    )

    @staticmethod
    def normalize_name(
        value: str,
    ) -> str:
        value = value.lower().strip()

        value = re.sub(
            r"[^a-z0-9]+",
            " ",
            value,
        )

        return re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

    @classmethod
    def brand_aliases(
        cls,
        brand_name: str,
    ) -> set[str]:
        aliases = {
            brand_name.strip(),
        }

        lower = brand_name.lower().strip()

        if lower.endswith(" ai"):
            aliases.add(
                brand_name[:-3].strip()
            )

        return {
            alias
            for alias in aliases
            if len(alias) >= 2
        }

    @staticmethod
    def occurrence_count(
        text: str,
        value: str,
    ) -> int:
        pattern = re.compile(
            rf"(?<!\w){re.escape(value)}(?!\w)",
            re.IGNORECASE,
        )

        return len(
            pattern.findall(text)
        )

    @staticmethod
    def first_position(
        text: str,
        value: str,
    ) -> int | None:
        match = re.search(
            rf"(?<!\w){re.escape(value)}(?!\w)",
            text,
            flags=re.IGNORECASE,
        )

        if match is None:
            return None

        return match.start()

    @classmethod
    def clean_candidate(
        cls,
        value: str,
    ) -> str | None:
        value = re.sub(
            r"[*_`]",
            "",
            value,
        ).strip()

        value = re.sub(
            r"^(choose|consider|use)\s+",
            "",
            value,
            flags=re.IGNORECASE,
        ).strip()

        value = re.sub(
            r"-type platforms?$",
            "",
            value,
            flags=re.IGNORECASE,
        ).strip()

        if not value:
            return None

        normalized = cls.normalize_name(
            value
        )

        if normalized in cls.CANDIDATE_STOPWORDS:
            return None

        if normalized.startswith(
            cls.PROTOCOL_PREFIXES
        ):
            return None

        generic_phrases = {
            "software separately from the chargers",
            "full charging backend",
            "charging backend",
            "consumer facing mobile app",
            "fleet energy platform",
        }

        if normalized in generic_phrases:
            return None

        if len(value.split()) > 4:
            return None

        if len(value) > 80:
            return None

        if not any(
            character.isupper()
            for character in value
        ):
            return None

        return value

    @classmethod
    def extract_candidates(
        cls,
        text: str,
    ) -> list[str]:
        raw_candidates = re.findall(
            r"\*\*([^*\n]{2,80})\*\*",
            text,
        )

        results: list[str] = []
        seen: set[str] = set()

        for raw in raw_candidates:
            raw = re.sub(
                r"^(choose|consider|use)\s+",
                "",
                raw.strip(),
                flags=re.IGNORECASE,
            )

            parts = re.split(
                r"\s+(?:or|/)\s+|\s*/\s*",
                raw,
                flags=re.IGNORECASE,
            )

            for part in parts:
                candidate = cls.clean_candidate(
                    part
                )

                if not candidate:
                    continue

                normalized = cls.normalize_name(
                    candidate
                )

                duplicate = any(
                    normalized == existing
                    or normalized.startswith(
                        existing + " "
                    )
                    or existing.startswith(
                        normalized + " "
                    )
                    for existing in seen
                )

                if duplicate:
                    continue

                seen.add(normalized)
                results.append(candidate)

        return results

    @classmethod
    def extract_urls_from_text(
        cls,
        text: str,
    ) -> list[dict]:
        urls = re.findall(
            r"https?://[^\s<>\]\)\"']+",
            text,
        )

        return [
            {
                "url": url.rstrip(".,;"),
                "title": None,
            }
            for url in urls
        ]

    @classmethod
    def extract_citation_annotations(
        cls,
        value,
    ) -> list[dict]:
        results: list[dict] = []

        def walk(node):
            if isinstance(node, dict):
                node_type = str(
                    node.get("type", "")
                ).lower()

                url = node.get("url")

                if (
                    url
                    and "citation" in node_type
                ):
                    results.append(
                        {
                            "url": url,
                            "title": node.get(
                                "title"
                            ),
                        }
                    )

                for child in node.values():
                    walk(child)

            elif isinstance(node, list):
                for child in node:
                    walk(child)

        walk(value)

        return results

    @classmethod
    def analyze(
        cls,
        db: Session,
        run_id: int,
    ) -> dict:
        run = AIRunRepository.get_by_id(
            db,
            run_id,
        )

        if run is None:
            raise HTTPException(
                status_code=404,
                detail="AI run not found.",
            )

        response = run.response

        if response is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "AI run has no response to analyze."
                ),
            )

        text = response.response_text

        VisibilityRepository.clear_response_analysis(
            db,
            response.id,
        )

        project_brand_rows = (
            ProjectBrandRepository.list_brand_roles(
                db,
                run.project_id,
            )
        )

        known_normalized: set[str] = set()

        detected: list[dict] = []

        brand_domains: dict[str, int] = {}

        for brand, role in project_brand_rows:

            for website in (
                WebsiteRepository.list_by_brand(
                    db,
                    brand.id,
                )
            ):
                brand_domains[
                    website.domain.lower()
                ] = brand.id

            aliases = cls.brand_aliases(
                brand.name
            )

            best_alias = None
            best_position = None
            total_count = 0

            for alias in aliases:
                count = cls.occurrence_count(
                    text,
                    alias,
                )

                position = cls.first_position(
                    text,
                    alias,
                )

                if count:
                    total_count += count

                    if (
                        best_position is None
                        or (
                            position is not None
                            and position < best_position
                        )
                    ):
                        best_position = position
                        best_alias = alias

            known_normalized.add(
                cls.normalize_name(
                    brand.name
                )
            )

            for alias in aliases:
                known_normalized.add(
                    cls.normalize_name(alias)
                )

            if best_alias is not None:
                detected.append(
                    {
                        "brand_id": brand.id,
                        "mention_text": best_alias,
                        "normalized_name":
                            cls.normalize_name(
                                brand.name
                            ),
                        "char_position":
                            best_position or 0,
                        "mention_count":
                            total_count,
                        "is_target":
                            role == "target",
                        "resolution_status":
                            "resolved",
                        "confidence": 1.0,
                    }
                )

        for candidate in cls.extract_candidates(
            text
        ):
            normalized = cls.normalize_name(
                candidate
            )

            if normalized in known_normalized:
                continue

            position = cls.first_position(
                text,
                candidate,
            )

            if position is None:
                continue

            detected.append(
                {
                    "brand_id": None,
                    "mention_text": candidate,
                    "normalized_name": normalized,
                    "char_position": position,
                    "mention_count":
                        cls.occurrence_count(
                            text,
                            candidate,
                        ),
                    "is_target": False,
                    "resolution_status":
                        "unresolved",
                    "confidence": 0.70,
                }
            )

        detected.sort(
            key=lambda item:
                item["char_position"]
        )

        seen: set[str] = set()
        mention_position = 1

        for item in detected:
            normalized = item[
                "normalized_name"
            ]

            if normalized in seen:
                continue

            seen.add(normalized)

            VisibilityRepository.create_mention(
                db=db,
                response_id=response.id,
                brand_id=item["brand_id"],
                mention_text=item[
                    "mention_text"
                ],
                normalized_name=normalized,
                position=mention_position,
                mention_count=item[
                    "mention_count"
                ],
                is_target=item[
                    "is_target"
                ],
                resolution_status=item[
                    "resolution_status"
                ],
                confidence=item[
                    "confidence"
                ],
            )

            mention_position += 1

        citations = (
            cls.extract_urls_from_text(text)
            + cls.extract_citation_annotations(
                response.raw_response
            )
        )

        seen_urls: set[str] = set()
        citation_position = 1

        for citation in citations:
            url = citation.get("url")

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)

            hostname = (
                urlparse(url).hostname
                or ""
            ).lower()

            if hostname.startswith("www."):
                hostname = hostname[4:]

            brand_id = brand_domains.get(
                hostname
            )

            VisibilityRepository.create_citation(
                db=db,
                response_id=response.id,
                brand_id=brand_id,
                url=url,
                domain=hostname or None,
                title=citation.get(
                    "title"
                ),
                position=citation_position,
            )

            citation_position += 1

        response.visibility_analyzed_at = datetime.now(
            timezone.utc
        )

        db.commit()

        mentions = (
            VisibilityRepository.list_mentions(
                db,
                response.id,
            )
        )

        stored_citations = (
            VisibilityRepository.list_citations(
                db,
                response.id,
            )
        )

        target_mentioned = any(
            mention.is_target
            for mention in mentions
        )

        target_brand_ids = {
            brand.id
            for brand, role
            in project_brand_rows
            if role == "target"
        }

        target_cited = any(
            citation.brand_id
            in target_brand_ids
            for citation in stored_citations
        )

        return {
            "run_id": run.id,
            "response_id": response.id,
            "target_mentioned":
                target_mentioned,
            "target_cited":
                target_cited,
            "mention_count":
                len(mentions),
            "citation_count":
                len(stored_citations),
            "mentions": mentions,
            "citations": stored_citations,
        }
