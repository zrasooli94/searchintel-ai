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
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.services.competitor_resolution_service import (
    CompetitorResolutionService,
)


class CandidateValidationService:

    @staticmethod
    def parse_json(
        text: str,
    ) -> dict:
        text = text.strip()

        text = re.sub(
            r"^```(?:json)?\\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\\s*```$",
            "",
            text,
        )

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(
                "Validator did not return JSON."
            )

        return json.loads(
            text[start:end + 1]
        )

    @staticmethod
    def get_mentions(
        db: Session,
        project_id: int,
        normalized_name: str,
    ) -> list[BrandMention]:
        statement = (
            select(BrandMention)
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
                AIRun.project_id == project_id,
                BrandMention.normalized_name
                == normalized_name,
                BrandMention.resolution_status.in_(
                    [
                        "unresolved",
                        "candidate",
                    ]
                ),
            )
        )

        return list(
            db.scalars(statement).all()
        )

    @classmethod
    def validate(
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

        candidates = (
            CompetitorResolutionService.list_candidates(
                db,
                project_id,
            )
        )[:limit]

        if not candidates:
            return {
                "project_id": project_id,
                "model_id": model_id,
                "evaluated_count": 0,
                "valid_count": 0,
                "rejected_count": 0,
                "undecided_count": 0,
                "valid_candidates": [],
                "rejected_candidates": [],
            }

        numbered = [
            {
                "id": index,
                "name": candidate["name"],
            }
            for index, candidate
            in enumerate(
                candidates,
                start=1,
            )
        ]

        prompt = f"""
You are validating candidate entities extracted
from AI answers for a GEO/search visibility platform.

Decide whether each candidate is a plausible
company, commercial brand, named software product,
named platform, or named service provider.

VALID examples:
Driivz
ChargePoint
Virta
Wallbox
Blink Charging

REJECT generic concepts, capabilities, headings,
categories, protocols, actions, metrics, descriptive
phrases, or combined lists of several brands.

Examples to REJECT:
Fleet
Operations
Load management
Best when
Hardware interoperability
Payments and billing
Driivz, AMPECO, GreenFlux
Multi-site management
OCPP

Be conservative.

Return ONLY valid JSON in exactly this structure:

{{
  "valid_ids": [1, 2],
  "rejected_ids": [3, 4]
}}

Every ID should appear in at most one list.
Do not invent IDs.

Candidates:

{json.dumps(numbered, ensure_ascii=False)}
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
                    "Candidate validation failed: "
                    f"{exc}"
                ),
            ) from exc

        valid_ids = {
            int(value)
            for value in payload.get(
                "valid_ids",
                []
            )
            if str(value).isdigit()
        }

        rejected_ids = {
            int(value)
            for value in payload.get(
                "rejected_ids",
                []
            )
            if str(value).isdigit()
        }

        valid_ids &= set(
            range(
                1,
                len(candidates) + 1,
            )
        )

        rejected_ids &= set(
            range(
                1,
                len(candidates) + 1,
            )
        )

        rejected_ids -= valid_ids

        valid_names = []
        rejected_names = []

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            mentions = cls.get_mentions(
                db,
                project_id,
                candidate[
                    "normalized_name"
                ],
            )

            if index in valid_ids:
                for mention in mentions:
                    mention.resolution_status = (
                        "candidate"
                    )
                    mention.confidence = max(
                        mention.confidence,
                        0.90,
                    )

                valid_names.append(
                    candidate["name"]
                )

            elif index in rejected_ids:
                for mention in mentions:
                    mention.resolution_status = (
                        "rejected"
                    )
                    mention.confidence = 0.0

                rejected_names.append(
                    candidate["name"]
                )

        db.commit()

        decided = (
            len(valid_ids)
            + len(rejected_ids)
        )

        return {
            "project_id": project_id,
            "model_id": model_id,
            "evaluated_count":
                len(candidates),
            "valid_count":
                len(valid_names),
            "rejected_count":
                len(rejected_names),
            "undecided_count":
                len(candidates) - decided,
            "valid_candidates":
                valid_names,
            "rejected_candidates":
                rejected_names,
        }
