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
from app.models.brand import Brand
from app.models.geo_prompt_opportunity import (
    GeoPromptOpportunity,
)
from app.repositories.ai_engine_repository import (
    AIEngineRepository,
)
from app.repositories.ai_model_repository import (
    AIModelRepository,
)
from app.repositories.geo_content_diagnosis_repository import (
    GeoContentDiagnosisRepository,
)
from app.services.content_evidence_service import (
    ContentEvidenceService,
)


class GeoContentDiagnosisService:

    @staticmethod
    def parse_json(
        value: str,
    ) -> dict:

        value = value.strip()

        value = re.sub(
            r"^```(?:json)?\s*",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(
            r"\s*```$",
            "",
            value,
        )

        start = value.find("{")
        end = value.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(
                "Diagnosis model did not return JSON."
            )

        return json.loads(
            value[start:end + 1]
        )

    @staticmethod
    def benchmark_evidence(
        db: Session,
        experiment_id: int,
        prompt_id: int,
        limit: int = 4,
    ) -> list[dict]:

        statement = (
            select(
                AIRun.id,
                AIResponse.response_text,
            )
            .join(
                AIResponse,
                AIResponse.run_id
                == AIRun.id,
            )
            .where(
                AIRun.experiment_id
                == experiment_id,
                AIRun.prompt_id
                == prompt_id,
                AIRun.include_in_metrics
                .is_(True),
                AIRun.status == "completed",
            )
            .order_by(AIRun.id)
            .limit(limit)
        )

        rows = list(
            db.execute(statement).all()
        )

        return [
            {
                "run_id": row.id,
                "response_excerpt":
                    row.response_text[:6000],
            }
            for row in rows
        ]

    @classmethod
    def diagnose(
        cls,
        db: Session,
        opportunity_id: int,
        model_id: int,
    ):

        opportunity = db.get(
            GeoPromptOpportunity,
            opportunity_id,
        )

        if opportunity is None:
            raise HTTPException(
                status_code=404,
                detail="GEO opportunity not found.",
            )

        target = db.get(
            Brand,
            opportunity.target_brand_id,
        )

        if target is None:
            raise HTTPException(
                status_code=404,
                detail="Target brand not found.",
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

        if not model.is_active:
            raise HTTPException(
                status_code=400,
                detail="AI model is inactive.",
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

        pages = (
            ContentEvidenceService.relevant_pages(
                db=db,
                brand_id=target.id,
                prompt=opportunity.prompt_text,
                limit=5,
            )
        )

        benchmark = cls.benchmark_evidence(
            db=db,
            experiment_id=
                opportunity.experiment_id,
            prompt_id=
                opportunity.prompt_id,
        )

        competitor_evidence = (
            opportunity.evidence or {}
        ).get(
            "competitors",
            [],
        )

        evidence_payload = {
            "target_brand":
                target.name,

            "prompt":
                opportunity.prompt_text,

            "category":
                opportunity.category,

            "intent":
                opportunity.intent,

            "gap_type":
                opportunity.gap_type,

            "opportunity_score":
                opportunity.opportunity_score,

            "target_mention_rate":
                opportunity.target_mention_rate,

            "top_competitor":
                opportunity.top_competitor_name,

            "competitor_visibility":
                competitor_evidence,

            "target_site_pages":
                pages,

            "benchmark_responses":
                benchmark,
        }

        instructions = """
You are the evidence-grounded GEO content
diagnosis engine for SearchIntel AI.

Your job is to diagnose why the target brand
may have weak visibility for the supplied prompt
and propose concrete content/entity improvements.

STRICT RULES:

1. Use ONLY the evidence supplied below.
2. Do not claim that visibility gaps are certainly
   caused by website content. State them as
   evidence-backed hypotheses.
3. Do not invent competitor website content.
4. Competitor evidence only proves visibility in
   the benchmark answers unless actual competitor
   page evidence is supplied.
5. Distinguish observations from recommendations.
6. If target website evidence is insufficient,
   explicitly say so.
7. Do not recommend keyword stuffing, fake reviews,
   fabricated statistics, deceptive link schemes,
   or invented customer proof.
8. Recommendations should help both humans and
   search/AI systems understand the brand clearly.

Return ONLY JSON with this structure:

{
  "diagnosis_summary": "...",

  "observed_evidence": [
    "..."
  ],

  "content_gaps": [
    {
      "gap": "...",
      "reason": "...",
      "evidence": "..."
    }
  ],

  "entity_gaps": [
    "..."
  ],

  "proof_gaps": [
    "..."
  ],

  "recommended_page": {
    "page_type": "...",
    "suggested_title": "...",
    "primary_intent": "...",
    "purpose": "...",
    "sections": [
      {
        "heading": "...",
        "goal": "..."
      }
    ]
  },

  "on_page_actions": [
    "..."
  ],

  "internal_link_actions": [
    "..."
  ],

  "structured_data_actions": [
    "..."
  ],

  "authority_actions": [
    "..."
  ],

  "measurement_plan": [
    "..."
  ],

  "evidence_limitations": [
    "..."
  ],

  "confidence": 0.0
}

confidence must be between 0 and 1.
"""

        prompt = (
            instructions
            + "\n\nEVIDENCE:\n"
            + json.dumps(
                evidence_payload,
                ensure_ascii=False,
                indent=2,
            )
        )

        try:
            provider = ProviderFactory.create(
                engine.slug
            )

            result = provider.execute(
                prompt=prompt,
                model_id=model.provider_model_id,
            )

            analysis = cls.parse_json(
                result.response_text
            )

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "GEO diagnosis failed: "
                    f"{exc}"
                ),
            ) from exc

        confidence = analysis.get(
            "confidence",
            0.0,
        )

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            ),
        )

        page_ids = [
            item["page_id"]
            for item in pages
        ]

        run_ids = [
            item["run_id"]
            for item in benchmark
        ]

        record = (
            GeoContentDiagnosisRepository.create(
                db=db,
                opportunity_id=
                    opportunity.id,
                experiment_id=
                    opportunity.experiment_id,
                project_id=
                    opportunity.project_id,
                target_brand_id=
                    target.id,
                model_id=
                    model.id,
                status="completed",
                confidence=
                    confidence,
                analysis=
                    analysis,
                evidence_page_ids=
                    page_ids,
                evidence_run_ids=
                    run_ids,
            )
        )

        db.commit()
        db.refresh(record)

        return record

    @staticmethod
    def latest(
        db: Session,
        opportunity_id: int,
    ):

        diagnosis = (
            GeoContentDiagnosisRepository.latest(
                db,
                opportunity_id,
            )
        )

        if diagnosis is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "No diagnosis exists "
                    "for this opportunity."
                ),
            )

        return diagnosis
