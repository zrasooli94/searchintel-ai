import json
import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.ai.provider_factory import (
    ProviderFactory,
)
from app.models.ai_response import AIResponse
from app.models.ai_run import AIRun
from app.models.brand_mention import BrandMention
from app.repositories.ai_engine_repository import (
    AIEngineRepository,
)
from app.repositories.ai_model_repository import (
    AIModelRepository,
)
from app.repositories.entity_resolution_rule_repository import (
    EntityResolutionRuleRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)


class EntityClassificationService:

    ALLOWED_ENTITY_TYPES = {
        "brand",
        "company",
        "product",
        "software_project",
        "organization",
        "service",
    }

    ALLOWED_RELATIONSHIPS = {
        "product_of",
        "owned_by",
        "operated_by",
        "service_of",
        "related_to",
    }

    @staticmethod
    def parse_json(
        text: str,
    ) -> dict:

        text = text.strip()

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

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(
                "Classifier did not return JSON."
            )

        return json.loads(
            text[start:end + 1]
        )

    @staticmethod
    def context_snippet(
        text: str,
        mention_text: str,
    ) -> str:

        lower_text = text.lower()
        lower_mention = mention_text.lower()

        position = lower_text.find(
            lower_mention
        )

        if position == -1:
            return text[:500].replace(
                "\n",
                " ",
            )

        start = max(
            0,
            position - 180,
        )

        end = min(
            len(text),
            position
            + len(mention_text)
            + 280,
        )

        return (
            text[start:end]
            .replace("\n", " ")
            .strip()
        )

    @classmethod
    def get_contexts(
        cls,
        db: Session,
        project_id: int,
        normalized_name: str,
    ) -> list[str]:

        rows = list(
            db.execute(
                select(
                    BrandMention,
                    AIResponse,
                )
                .join(
                    AIResponse,
                    BrandMention.response_id
                    == AIResponse.id,
                )
                .join(
                    AIRun,
                    AIResponse.run_id
                    == AIRun.id,
                )
                .where(
                    AIRun.project_id
                    == project_id,
                    BrandMention.normalized_name
                    == normalized_name,
                )
                .order_by(
                    AIResponse.id.desc()
                )
                .limit(3)
            ).all()
        )

        contexts = []

        for mention, response in rows:
            contexts.append(
                cls.context_snippet(
                    response.response_text,
                    mention.mention_text,
                )
            )

        return contexts

    @classmethod
    def list_candidates(
        cls,
        db: Session,
        project_id: int,
    ) -> list[dict]:

        rules = (
            EntityResolutionRuleRepository
            .list_by_status(
                db,
                project_id,
                "candidate",
            )
        )

        return [
            {
                "rule_id": rule.id,
                "name": (
                    rule.display_name
                    or rule.normalized_name
                ),
                "normalized_name":
                    rule.normalized_name,
                "status": rule.status,
                "entity_type":
                    rule.entity_type,
                "proposed_parent_name":
                    rule.proposed_parent_name,
                "proposed_relationship_type":
                    rule.proposed_relationship_type,
                "classification_confidence":
                    rule.classification_confidence,
                "classification_source":
                    rule.classification_source,
            }
            for rule in rules
        ]

    @classmethod
    def classify(
        cls,
        db: Session,
        project_id: int,
        model_id: int,
        limit: int,
    ) -> dict:

        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        model = AIModelRepository.get_by_id(
            db,
            model_id,
        )

        if model is None:
            raise HTTPException(
                status_code=404,
                detail="AI model not found.",
            )

        engine = AIEngineRepository.get_by_id(
            db,
            model.engine_id,
        )

        if engine is None:
            raise HTTPException(
                status_code=404,
                detail="AI engine not found.",
            )

        rules = (
            EntityResolutionRuleRepository
            .list_by_status(
                db,
                project_id,
                "candidate",
            )
        )[:limit]

        if not rules:
            return {
                "project_id": project_id,
                "model_id": model_id,
                "classified_count": 0,
                "skipped_count": 0,
                "classifications": [],
            }

        candidates = []

        for index, rule in enumerate(
            rules,
            start=1,
        ):

            candidates.append(
                {
                    "id": index,
                    "name": (
                        rule.display_name
                        or rule.normalized_name
                    ),
                    "contexts":
                        cls.get_contexts(
                            db,
                            project_id,
                            rule.normalized_name,
                        ),
                }
            )

        prompt = f"""
You are performing entity typing for a search
intelligence and GEO knowledge graph.

Classify each candidate using exactly ONE type:

brand
- a market-facing commercial brand name.

company
- a company, legal/commercial business, consultancy,
  operator, service provider, or corporate entity.

product
- a named product, platform, application, product line,
  or software offering belonging to another entity.

software_project
- a named open-source or independent software project
  that should not automatically be treated as a
  commercial competitor brand.

organization
- a standards body, government body, nonprofit,
  association, research organization, or similar entity.

service
- a specifically named service offering rather than
  the company that provides it.

Parent relationships:
- If there is strong evidence that a candidate belongs
  to another named entity, provide parent_name and one
  relationship_type.
- Allowed relationship_type values:
  product_of
  owned_by
  operated_by
  service_of
  related_to
- If the parent is unclear, use null for both fields.
- Never infer a parent merely because names look similar.
- Do NOT merge similarly named entities.
- "ChargeOps AI", "ChargeOps", "ChargeOS", and
  "ChargeOps Cloud" may represent different entities.
- Prefer null over guessing.

Examples:
PowerFlex X
→ product
→ parent PowerFlex
→ product_of

ChargePilot
→ product
→ parent The Mobility House
→ product_of

CitrineOS
→ software_project
→ parent null

Return ONLY JSON:

{{
  "items": [
    {{
      "id": 1,
      "entity_type": "product",
      "parent_name": "Example Parent",
      "relationship_type": "product_of",
      "confidence": 0.95
    }}
  ]
}}

Every candidate ID should appear at most once.
Confidence must be between 0 and 1.

Candidates with evidence:

{json.dumps(
    candidates,
    ensure_ascii=False,
    indent=2,
)}
"""

        try:
            provider = ProviderFactory.create(
                engine.slug
            )

            result = provider.execute(
                prompt=prompt,
                model_id=model.provider_model_id,
            )

            payload = cls.parse_json(
                result.response_text
            )

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Entity classification failed: "
                    f"{exc}"
                ),
            ) from exc

        returned_items = (
            payload.get("items") or []
        )

        by_id = {}

        for item in returned_items:

            try:
                item_id = int(
                    item.get("id")
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if not (
                1
                <= item_id
                <= len(rules)
            ):
                continue

            entity_type = str(
                item.get(
                    "entity_type",
                    "",
                )
            ).strip()

            if (
                entity_type
                not in cls.ALLOWED_ENTITY_TYPES
            ):
                continue

            parent_name = item.get(
                "parent_name"
            )

            if isinstance(
                parent_name,
                str,
            ):
                parent_name = (
                    parent_name.strip()
                    or None
                )
            else:
                parent_name = None

            relationship_type = (
                item.get(
                    "relationship_type"
                )
            )

            if (
                relationship_type
                not in cls.ALLOWED_RELATIONSHIPS
            ):
                relationship_type = None

            if parent_name is None:
                relationship_type = None

            try:
                confidence = float(
                    item.get(
                        "confidence",
                        0.5,
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                confidence = 0.5

            confidence = max(
                0.0,
                min(
                    1.0,
                    confidence,
                ),
            )

            by_id[item_id] = {
                "entity_type":
                    entity_type,
                "parent_name":
                    parent_name,
                "relationship_type":
                    relationship_type,
                "confidence":
                    confidence,
            }

        classifications = []

        for index, rule in enumerate(
            rules,
            start=1,
        ):

            item = by_id.get(index)

            if item is None:
                continue

            (
                EntityResolutionRuleRepository
                .set_classification(
                    db=db,
                    rule=rule,
                    entity_type=item[
                        "entity_type"
                    ],
                    proposed_parent_name=item[
                        "parent_name"
                    ],
                    proposed_relationship_type=item[
                        "relationship_type"
                    ],
                    classification_confidence=item[
                        "confidence"
                    ],
                    classification_source=(
                        "ai_entity_classifier"
                    ),
                )
            )

            classifications.append(
                {
                    "rule_id":
                        rule.id,
                    "name":
                        (
                            rule.display_name
                            or rule.normalized_name
                        ),
                    "normalized_name":
                        rule.normalized_name,
                    "entity_type":
                        item["entity_type"],
                    "proposed_parent_name":
                        item["parent_name"],
                    "proposed_relationship_type":
                        item[
                            "relationship_type"
                        ],
                    "confidence":
                        item["confidence"],
                }
            )

        db.commit()

        return {
            "project_id":
                project_id,
            "model_id":
                model_id,
            "classified_count":
                len(classifications),
            "skipped_count":
                len(rules)
                - len(classifications),
            "classifications":
                classifications,
        }
