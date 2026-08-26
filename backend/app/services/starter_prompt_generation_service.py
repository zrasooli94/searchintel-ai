import json
import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.integrations.ai.provider_factory import (
    ProviderFactory,
)
from app.models.ai_model import AIModel

from app.repositories.ai_engine_repository import (
    AIEngineRepository,
)
from app.repositories.page_repository import (
    PageRepository,
)
from app.repositories.project_brand_repository import (
    ProjectBrandRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.repositories.prompt_repository import (
    PromptRepository,
)
from app.repositories.website_repository import (
    WebsiteRepository,
)

from app.services.ai_model_service import AIModelService


class StarterPromptGenerationService:

    VALID_CATEGORIES = {
        "informational",
        "navigational",
        "commercial",
        "transactional",
        "comparison",
        "recommendation",
        "problem_solution",
        "brand",
    }

    @staticmethod
    def normalize_text(
        value: str,
    ) -> str:
        return re.sub(
            r"\s+",
            " ",
            value.strip().lower(),
        )

    @classmethod
    def choose_model(
        cls,
        db: Session,
        model_id: int | None,
    ):
        return AIModelService.resolve_execution_model(
            db,
            model_id,
        )

    @staticmethod
    def extract_json(
        response_text: str,
    ) -> dict:
        text = response_text.strip()

        if text.startswith("```"):
            text = re.sub(
                r"^```(?:json)?\s*",
                "",
                text,
                flags=re.IGNORECASE,
            )

            text = re.sub(
                r"\s*```$",
                "",
                text,
            )

        try:
            value = json.loads(
                text
            )

            if isinstance(
                value,
                dict,
            ):
                return value

        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")

        if (
            start == -1
            or end == -1
            or end <= start
        ):
            raise HTTPException(
                status_code=502,
                detail=(
                    "AI prompt generator did "
                    "not return valid JSON."
                ),
            )

        try:
            value = json.loads(
                text[
                    start:
                    end + 1
                ]
            )

        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "AI prompt generator returned "
                    "malformed JSON."
                ),
            ) from exc

        if not isinstance(
            value,
            dict,
        ):
            raise HTTPException(
                status_code=502,
                detail=(
                    "Unexpected generator "
                    "response format."
                ),
            )

        return value

    @classmethod
    def generate(
        cls,
        db: Session,
        project_id: int,
        count: int,
        model_id: int | None = None,
    ) -> dict:

        project = (
            ProjectRepository.get_by_id(
                db,
                project_id,
            )
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        brand_roles = (
            ProjectBrandRepository
            .list_brand_roles(
                db,
                project_id,
            )
        )

        targets = [
            brand
            for brand, role
            in brand_roles
            if role == "target"
        ]

        if not targets:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Project has no target brand."
                ),
            )

        target = targets[0]

        competitors = [
            brand
            for brand, role
            in brand_roles
            if role == "competitor"
        ]

        websites = (
            WebsiteRepository.list_by_brand(
                db,
                target.id,
            )
        )

        primary = next(
            (
                website
                for website in websites
                if website.is_primary
            ),
            None,
        )

        website = (
            primary
            or (
                websites[0]
                if websites
                else None
            )
        )

        if website is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Target brand has no website."
                ),
            )

        pages = (
            PageRepository.list_by_website(
                db,
                website.id,
            )
        )

        if not pages:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Crawl the target website "
                    "before generating prompts."
                ),
            )

        existing_prompts = (
            PromptRepository
            .list_by_project(
                db,
                project_id,
            )
        )

        existing_texts = {
            cls.normalize_text(
                prompt.text
            )
            for prompt in existing_prompts
        }

        page_sections = []

        total_chars = 0
        max_chars = 18000

        sorted_pages = sorted(
            pages,
            key=lambda page:
                (
                    page.word_count
                    or 0
                ),
            reverse=True,
        )

        pages_used = 0

        for page in sorted_pages:
            content = (
                page.content_text
                or ""
            ).strip()

            if not content:
                continue

            excerpt = content[:2500]

            section = (
                f"URL: {page.url}\n"
                f"Title: {page.title or ''}\n"
                f"H1: {page.h1 or ''}\n"
                f"Content excerpt:\n"
                f"{excerpt}"
            )

            if (
                total_chars
                + len(section)
                > max_chars
            ):
                break

            page_sections.append(
                section
            )

            total_chars += len(
                section
            )

            pages_used += 1

        if not page_sections:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Crawled pages contain no "
                    "usable content."
                ),
            )

        competitor_names = [
            brand.name
            for brand
            in competitors
        ]

        existing_block = (
            "\n".join(
                f"- {prompt.text}"
                for prompt
                in existing_prompts
            )
            or "(none)"
        )

        website_block = (
            "\n\n--- PAGE ---\n\n"
        ).join(
            page_sections
        )

        competitor_block = (
            ", ".join(
                competitor_names
            )
            or "(none configured)"
        )

        generation_prompt = f"""
You are designing a controlled AI-search visibility benchmark.

Create exactly {count} realistic prompts that a buyer, operator, evaluator, or researcher could ask an AI assistant when exploring the category represented by the target website.

TARGET BRAND:
{target.name}

CONFIGURED COMPETITORS:
{competitor_block}

EXISTING STORED PROMPTS TO AVOID DUPLICATING:
{existing_block}

TARGET WEBSITE EVIDENCE:
{website_block}

REQUIREMENTS:

1. Return valid JSON only.
2. Do not use markdown fences.
3. Output this exact top-level structure:

{{
  "prompts": [
    {{
      "text": "...",
      "category": "commercial",
      "rationale": "..."
    }}
  ]
}}

4. Allowed categories:
informational
navigational
commercial
transactional
comparison
recommendation
problem_solution
brand

5. Favor these categories:
informational
commercial
comparison
recommendation
problem_solution
brand

6. The benchmark must test discovery, not just branded recall.

7. At least 70% of prompts must NOT mention the target brand by name.

8. Use no more than 2 target-brand-specific prompts.

9. Comparison prompts may mention configured competitors when natural, but do not force competitor names into every prompt.

10. Prompts should sound like genuine AI-search questions, not SEO keywords.

11. Include both:
- category-level discovery questions
- concrete operational/problem questions

12. Do not invent capabilities that are not supported by the supplied target website evidence.

13. Avoid duplicates and near-duplicates.

14. Do not duplicate the existing stored prompts listed above.

15. Each rationale should be one short sentence explaining what visibility behavior the prompt measures.
""".strip()

        model = cls.choose_model(
            db,
            model_id,
        )

        engine = (
            AIEngineRepository.get_by_id(
                db,
                model.engine_id,
            )
        )

        if engine is None:
            raise HTTPException(
                status_code=500,
                detail=(
                    "AI model engine "
                    "could not be resolved."
                ),
            )

        try:
            provider = (
                ProviderFactory.create(
                    engine.slug
                )
            )

            result = provider.execute(
                prompt=generation_prompt,
                model_id=
                    model.provider_model_id,
                mode="memory",
            )

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "AI starter prompt "
                    f"generation failed: {exc}"
                ),
            ) from exc

        payload = cls.extract_json(
            result.response_text
        )

        raw_prompts = (
            payload.get(
                "prompts"
            )
        )

        if not isinstance(
            raw_prompts,
            list,
        ):
            raise HTTPException(
                status_code=502,
                detail=(
                    "Generator response did not "
                    "contain a prompt list."
                ),
            )

        output = []
        seen = set()

        for item in raw_prompts:
            if not isinstance(
                item,
                dict,
            ):
                continue

            text = str(
                item.get(
                    "text",
                    "",
                )
            ).strip()

            category = str(
                item.get(
                    "category",
                    "",
                )
            ).strip().lower()

            rationale_value = (
                item.get(
                    "rationale"
                )
            )

            rationale = (
                str(
                    rationale_value
                ).strip()
                if rationale_value
                else None
            )

            if len(text) < 5:
                continue

            if (
                category
                not in cls.VALID_CATEGORIES
            ):
                continue

            normalized = (
                cls.normalize_text(
                    text
                )
            )

            if (
                normalized
                in existing_texts
                or normalized
                in seen
            ):
                continue

            seen.add(
                normalized
            )

            output.append(
                {
                    "text":
                        text,

                    "category":
                        category,

                    "rationale":
                        rationale,
                }
            )

            if len(output) >= count:
                break

        if len(output) < 6:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Generator returned too few "
                    "valid unique prompts."
                ),
            )

        return {
            "project_id":
                project_id,

            "model_id":
                model.id,

            "model_name":
                model.name,

            "provider_model_id":
                model.provider_model_id,

            "target_brand":
                target.name,

            "website_pages_used":
                pages_used,

            "competitors_used":
                competitor_names,

            "existing_prompts_considered":
                len(
                    existing_prompts
                ),

            "requested_count":
                count,

            "generated_count":
                len(output),

            "prompts":
                output,
        }
