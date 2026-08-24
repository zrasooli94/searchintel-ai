import re

from datetime import datetime, timezone

from urllib.parse import (
    parse_qsl,
    urlencode,
    urlparse,
    urlunparse,
)

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.brand_alias_repository import (
    BrandAliasRepository,
)
from app.repositories.entity_resolution_rule_repository import (
    EntityResolutionRuleRepository,
)
from app.repositories.search_entity_repository import (
    SearchEntityRepository,
)
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
    def normalize_hostname(
        hostname: str | None,
    ) -> str:

        value = (
            hostname or ""
        ).lower().strip(".")

        if value.startswith("www."):
            value = value[4:]

        return value

    @classmethod
    def normalize_url_for_match(
        cls,
        url: str,
    ) -> str:

        parsed = urlparse(url)

        hostname = cls.normalize_hostname(
            parsed.hostname
        )

        tracking_keys = {
            "gclid",
            "fbclid",
            "msclkid",
        }

        query_items = [
            (key, value)
            for key, value
            in parse_qsl(
                parsed.query,
                keep_blank_values=True,
            )
            if not key.lower().startswith(
                "utm_"
            )
            and key.lower()
            not in tracking_keys
        ]

        normalized_query = urlencode(
            sorted(query_items)
        )

        path = parsed.path or "/"

        if path != "/":
            path = path.rstrip("/")

        return urlunparse(
            (
                parsed.scheme.lower()
                or "https",
                hostname,
                path,
                "",
                normalized_query,
                "",
            )
        )

    @classmethod
    def resolve_brand_for_hostname(
        cls,
        hostname: str,
        domain_brand_pairs:
            list[tuple[str, int]],
    ) -> int | None:

        hostname = cls.normalize_hostname(
            hostname
        )

        matches: list[
            tuple[int, int]
        ] = []

        for domain, brand_id in (
            domain_brand_pairs
        ):
            normalized_domain = (
                cls.normalize_hostname(
                    domain
                )
            )

            if (
                hostname
                == normalized_domain
                or hostname.endswith(
                    "." + normalized_domain
                )
            ):
                matches.append(
                    (
                        len(
                            normalized_domain
                        ),
                        brand_id,
                    )
                )

        if not matches:
            return None

        longest = max(
            length
            for length, _
            in matches
        )

        brand_ids = {
            brand_id
            for length, brand_id
            in matches
            if length == longest
        }

        if len(brand_ids) != 1:
            return None

        return next(
            iter(brand_ids)
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
        return {
            brand_name.strip()
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
    def extract_web_search_sources(
        cls,
        value,
    ) -> list[dict]:

        results: list[dict] = []

        output = (
            value.get("output", [])
            if isinstance(value, dict)
            else []
        )

        search_call_index = 0

        for item in output:
            if not isinstance(
                item,
                dict,
            ):
                continue

            if (
                item.get("type")
                != "web_search_call"
            ):
                continue

            action = (
                item.get("action")
                or {}
            )

            sources = (
                action.get("sources")
                or []
            )

            if not sources:
                continue

            search_call_index += 1

            query = action.get("query")

            if isinstance(query, list):
                query = " | ".join(
                    str(value)
                    for value in query
                )

            elif query is not None:
                query = str(query)

            for index, source in enumerate(
                sources,
                start=1,
            ):
                if not isinstance(
                    source,
                    dict,
                ):
                    continue

                url = source.get("url")

                if not url:
                    continue

                results.append(
                    {
                        "search_call_index":
                            search_call_index,
                        "source_position":
                            index,
                        "search_query":
                            query,
                        "url":
                            url,
                        "title":
                            source.get(
                                "title"
                            ),
                    }
                )

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

        target_brand_ids = {
            brand.id
            for brand, role in project_brand_rows
            if role == "target"
        }

        brand_entity_ids: dict[int, int] = {}

        for brand, _role in project_brand_rows:
            entity = (
                SearchEntityRepository
                .get_brand_entity_by_brand_id(
                    db,
                    brand.id,
                )
            )

            if entity is not None:
                brand_entity_ids[
                    brand.id
                ] = entity.id

        known_normalized: set[str] = set()

        detected: list[dict] = []

        domain_brand_pairs = (
            WebsiteRepository
            .list_domain_brand_pairs_by_project(
                db,
                run.project_id,
            )
        )

        for brand, role in project_brand_rows:

            aliases = cls.brand_aliases(
                brand.name
            )

            for alias_record in (
                BrandAliasRepository.list_by_brand(
                    db,
                    brand.id,
                )
            ):
                aliases.add(
                    alias_record.alias
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
                        "entity_id":
                            brand_entity_ids.get(
                                brand.id
                            ),
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

            rule = (
                EntityResolutionRuleRepository.get(
                    db,
                    run.project_id,
                    normalized,
                )
            )

            brand_id = None
            entity_id = None
            resolution_status = "unresolved"
            confidence = 0.70
            is_target = False

            if rule is not None:
                resolution_status = rule.status
                brand_id = rule.brand_id
                entity_id = rule.entity_id
                confidence = rule.confidence

                # Backward compatibility for any
                # older resolved brand-only rule.
                if (
                    entity_id is None
                    and brand_id is not None
                ):
                    entity_id = (
                        brand_entity_ids.get(
                            brand_id
                        )
                    )

                # A resolved rule must now point to
                # an exact SearchEntity. brand_id
                # may legitimately be null for an
                # entity with no brand roll-up.
                if (
                    resolution_status == "resolved"
                    and entity_id is None
                ):
                    resolution_status = "unresolved"
                    confidence = 0.70

                if brand_id is not None:
                    is_target = (
                        brand_id
                        in target_brand_ids
                    )

            detected.append(
                {
                    "brand_id": brand_id,
                    "entity_id": entity_id,
                    "mention_text": candidate,
                    "normalized_name":
                        normalized,
                    "char_position":
                        position,
                    "mention_count":
                        cls.occurrence_count(
                            text,
                            candidate,
                        ),
                    "is_target":
                        is_target,
                    "resolution_status":
                        resolution_status,
                    "confidence":
                        confidence,
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
                entity_id=item.get(
                    "entity_id"
                ),
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

            hostname = cls.normalize_hostname(
                urlparse(url).hostname
            )

            brand_id = (
                cls.resolve_brand_for_hostname(
                    hostname,
                    domain_brand_pairs,
                )
            )

            entity_id = (
                brand_entity_ids.get(
                    brand_id
                )
                if brand_id is not None
                else None
            )

            VisibilityRepository.create_citation(
                db=db,
                response_id=response.id,
                brand_id=brand_id,
                entity_id=entity_id,
                url=url,
                domain=hostname or None,
                title=citation.get(
                    "title"
                ),
                position=citation_position,
            )

            citation_position += 1

        stored_citation_urls = {
            cls.normalize_url_for_match(
                citation.url
            )
            for citation in (
                VisibilityRepository.list_citations(
                    db,
                    response.id,
                )
            )
        }

        web_sources = (
            cls.extract_web_search_sources(
                response.raw_response or {}
            )
        )

        for source in web_sources:
            url = source["url"]

            hostname = cls.normalize_hostname(
                urlparse(url).hostname
            )

            brand_id = (
                cls.resolve_brand_for_hostname(
                    hostname,
                    domain_brand_pairs,
                )
            )

            entity_id = (
                brand_entity_ids.get(
                    brand_id
                )
                if brand_id is not None
                else None
            )

            normalized_url = (
                cls.normalize_url_for_match(
                    url
                )
            )

            VisibilityRepository.create_web_search_source(
                db=db,
                response_id=response.id,
                brand_id=brand_id,
                entity_id=entity_id,
                search_call_index=source[
                    "search_call_index"
                ],
                source_position=source[
                    "source_position"
                ],
                search_query=source[
                    "search_query"
                ],
                url=url,
                domain=hostname or None,
                title=source["title"],
                is_cited=(
                    normalized_url
                    in stored_citation_urls
                ),
            )

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

        stored_web_sources = (
            VisibilityRepository
            .list_web_search_sources(
                db,
                response.id,
            )
        )

        target_source_present = any(
            source.brand_id
            in target_brand_ids
            for source in stored_web_sources
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
            "web_search_source_count":
                len(stored_web_sources),
            "target_source_present":
                target_source_present,
            "mentions": mentions,
            "citations": stored_citations,
            "web_search_sources":
                stored_web_sources,
        }
