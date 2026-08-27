import math
import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.retrieval_versions import (
    SITE_RAG_RETRIEVAL_VERSION,
)
from app.models.page import Page
from app.models.project_brand import ProjectBrand
from app.models.website import Website


class SiteRAGRetrievalService:

    CHUNK_WORDS = 180
    CHUNK_OVERLAP = 40

    DEFAULT_TOP_K = 5
    MAX_TOP_K = 12
    MAX_CHUNKS_PER_PAGE = 2

    BM25_K1 = 1.5
    BM25_B = 0.75

    STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "this",
        "to",
        "use",
        "uses",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
    }

    @staticmethod
    def normalize_text(
        value: str | None,
    ) -> str:
        return re.sub(
            r"\s+",
            " ",
            value or "",
        ).strip()

    @classmethod
    def tokenize(
        cls,
        value: str | None,
    ) -> list[str]:
        raw_tokens = re.findall(
            r"[a-z0-9][a-z0-9_-]*",
            (value or "").lower(),
        )

        tokens: list[str] = []

        for token in raw_tokens:
            if (
                token in cls.STOPWORDS
                or len(token) <= 1
            ):
                continue

            if (
                len(token) > 4
                and token.endswith("s")
                and not token.endswith("ss")
            ):
                token = token[:-1]

            tokens.append(token)

        return tokens

    @classmethod
    def chunk_text(
        cls,
        value: str,
    ) -> list[tuple[int, str]]:
        normalized = cls.normalize_text(
            value
        )

        if not normalized:
            return []

        words = normalized.split()

        if len(words) <= cls.CHUNK_WORDS:
            return [
                (
                    0,
                    normalized,
                )
            ]

        step = (
            cls.CHUNK_WORDS
            - cls.CHUNK_OVERLAP
        )

        chunks: list[
            tuple[int, str]
        ] = []

        chunk_index = 0

        for start in range(
            0,
            len(words),
            step,
        ):
            end = min(
                start + cls.CHUNK_WORDS,
                len(words),
            )

            excerpt = " ".join(
                words[start:end]
            )

            if excerpt:
                chunks.append(
                    (
                        chunk_index,
                        excerpt,
                    )
                )

                chunk_index += 1

            if end >= len(words):
                break

        return chunks

    @staticmethod
    def target_website(
        db: Session,
        project_id: int,
    ) -> Website | None:
        statement = (
            select(Website)
            .join(
                ProjectBrand,
                ProjectBrand.brand_id
                == Website.brand_id,
            )
            .where(
                ProjectBrand.project_id
                == project_id,
                ProjectBrand.role
                == "target",
            )
            .order_by(
                Website.is_primary.desc(),
                Website.id,
            )
            .limit(1)
        )

        return db.scalar(statement)

    @staticmethod
    def website_pages(
        db: Session,
        website_id: int,
    ) -> list[Page]:
        statement = (
            select(Page)
            .where(
                Page.website_id
                == website_id,
                Page.status_code >= 200,
                Page.status_code < 300,
                Page.content_text
                .is_not(None),
                Page.content_text != "",
            )
            .order_by(Page.id)
        )

        return list(
            db.scalars(
                statement
            ).all()
        )

    @classmethod
    def build_grounded_prompt(
        cls,
        query: str,
        sources: list[dict],
    ) -> str:
        if sources:
            evidence_blocks = []

            for source in sources:
                evidence_blocks.append(
                    "\n".join(
                        [
                            (
                                f"[Source "
                                f"{source['rank']}]"
                            ),
                            (
                                f"URL: "
                                f"{source['url']}"
                            ),
                            (
                                f"Title: "
                                f"{source['title'] or 'Untitled'}"
                            ),
                            "Evidence:",
                            source["excerpt"],
                        ]
                    )
                )

            evidence = (
                "\n\n".join(
                    evidence_blocks
                )
            )
        else:
            evidence = (
                "No sufficiently relevant "
                "first-party evidence was "
                "retrieved."
            )

        return f"""You are answering a controlled Site RAG benchmark.

Use only the first-party website evidence provided below.

Rules:
- Do not use outside knowledge.
- Do not invent unsupported capabilities or facts.
- If the evidence is insufficient, say that clearly.
- Cite supporting passages inline using [Source N].
- Answer the user's question directly and concisely.

USER QUESTION:
{query}

FIRST-PARTY WEBSITE EVIDENCE:
{evidence}
"""

    @classmethod
    def retrieve(
        cls,
        db: Session,
        project_id: int,
        query: str,
        top_k: int | None = None,
    ) -> dict:
        limit = (
            top_k
            if top_k is not None
            else cls.DEFAULT_TOP_K
        )

        if (
            limit < 1
            or limit > cls.MAX_TOP_K
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Site RAG top_k must be "
                    f"between 1 and "
                    f"{cls.MAX_TOP_K}."
                ),
            )

        website = cls.target_website(
            db=db,
            project_id=project_id,
        )

        if website is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Project has no target "
                    "website for Site RAG."
                ),
            )

        pages = cls.website_pages(
            db=db,
            website_id=website.id,
        )

        if not pages:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Target website has no "
                    "crawled text content."
                ),
            )

        query_tokens = cls.tokenize(
            query
        )

        query_terms = set(
            query_tokens
        )

        records: list[dict] = []

        for page in pages:
            metadata = " ".join(
                filter(
                    None,
                    [
                        page.title,
                        page.h1,
                        page.meta_description,
                    ],
                )
            )

            metadata_tokens = set(
                cls.tokenize(metadata)
            )

            for (
                chunk_index,
                excerpt,
            ) in cls.chunk_text(
                page.content_text or ""
            ):
                tokens = cls.tokenize(
                    excerpt
                )

                if not tokens:
                    continue

                records.append(
                    {
                        "page":
                            page,

                        "chunk_index":
                            chunk_index,

                        "excerpt":
                            excerpt,

                        "tokens":
                            tokens,

                        "terms":
                            set(tokens),

                        "metadata_terms":
                            metadata_tokens,
                    }
                )

        if not records or not query_terms:
            return {
                "retrieval_version":
                    SITE_RAG_RETRIEVAL_VERSION,

                "project_id":
                    project_id,

                "website_id":
                    website.id,

                "domain":
                    website.domain,

                "query":
                    query,

                "pages_considered":
                    len(pages),

                "chunks_considered":
                    len(records),

                "sources":
                    [],
            }

        total_documents = len(records)

        average_length = (
            sum(
                len(record["tokens"])
                for record in records
            )
            / total_documents
        )

        document_frequency = {
            term: sum(
                1
                for record in records
                if term in record["terms"]
            )
            for term in query_terms
        }

        idf = {
            term: math.log(
                1
                + (
                    total_documents
                    - document_frequency[term]
                    + 0.5
                )
                / (
                    document_frequency[term]
                    + 0.5
                )
            )
            for term in query_terms
        }

        scored: list[dict] = []

        query_lower = query.lower()

        for record in records:
            tokens = record[
                "tokens"
            ]

            document_length = len(
                tokens
            )

            raw_score = 0.0

            for term in query_terms:
                frequency = tokens.count(
                    term
                )

                if frequency == 0:
                    continue

                numerator = (
                    frequency
                    * (
                        cls.BM25_K1
                        + 1
                    )
                )

                denominator = (
                    frequency
                    + cls.BM25_K1
                    * (
                        1
                        - cls.BM25_B
                        + cls.BM25_B
                        * (
                            document_length
                            / max(
                                average_length,
                                1.0,
                            )
                        )
                    )
                )

                raw_score += (
                    idf[term]
                    * numerator
                    / denominator
                )

            metadata_matches = (
                query_terms
                & record[
                    "metadata_terms"
                ]
            )

            raw_score += (
                sum(
                    idf[term]
                    for term
                    in metadata_matches
                )
                * 0.45
            )

            excerpt_lower = record[
                "excerpt"
            ].lower()

            phrase_boost = 0.0

            for phrase in (
                "human approval",
                "human-in-the-loop",
                "retrieval augmented",
                "retrieval-augmented",
                "ai agent",
                "ev charging",
            ):
                if (
                    phrase in query_lower
                    and phrase
                    in excerpt_lower
                ):
                    phrase_boost += 0.35

            # RAG is useful as a concept token
            # even though it is not a phrase.
            if (
                "rag" in query_terms
                and "rag"
                in record["terms"]
            ):
                phrase_boost += 0.25

            raw_score += min(
                phrase_boost,
                1.0,
            )

            if raw_score <= 0:
                continue

            page = record[
                "page"
            ]

            scored.append(
                {
                    "page_id":
                        page.id,

                    "chunk_index":
                        record[
                            "chunk_index"
                        ],

                    "raw_score":
                        raw_score,

                    "url":
                        (
                            page.canonical_url
                            or page.url
                        ),

                    "title":
                        page.title,

                    "excerpt":
                        record[
                            "excerpt"
                        ],
                }
            )

        scored.sort(
            key=lambda item: (
                -item["raw_score"],
                item["page_id"],
                item["chunk_index"],
            )
        )

        best_score = (
            scored[0]["raw_score"]
            if scored
            else 1.0
        )

        selected: list[dict] = []

        page_counts: dict[
            int,
            int,
        ] = {}

        for candidate in scored:
            page_id = candidate[
                "page_id"
            ]

            current_count = (
                page_counts.get(
                    page_id,
                    0,
                )
            )

            if (
                current_count
                >= cls.MAX_CHUNKS_PER_PAGE
            ):
                continue

            normalized_score = (
                candidate["raw_score"]
                / best_score
            )

            selected.append(
                {
                    "page_id":
                        candidate[
                            "page_id"
                        ],

                    "chunk_index":
                        candidate[
                            "chunk_index"
                        ],

                    "relevance_score":
                        round(
                            normalized_score,
                            6,
                        ),

                    "url":
                        candidate[
                            "url"
                        ],

                    "title":
                        candidate[
                            "title"
                        ],

                    "excerpt":
                        candidate[
                            "excerpt"
                        ],
                }
            )

            page_counts[
                page_id
            ] = (
                current_count + 1
            )

            if len(selected) >= limit:
                break

        for rank, source in enumerate(
            selected,
            start=1,
        ):
            source["rank"] = rank

        return {
            "retrieval_version":
                SITE_RAG_RETRIEVAL_VERSION,

            "project_id":
                project_id,

            "website_id":
                website.id,

            "domain":
                website.domain,

            "query":
                query,

            "pages_considered":
                len(pages),

            "chunks_considered":
                len(records),

            "sources":
                selected,
        }
