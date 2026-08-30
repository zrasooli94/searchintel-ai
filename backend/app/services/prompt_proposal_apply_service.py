from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt import Prompt
from app.models.prompt_set_proposal import PromptSetProposal
from app.services.starter_prompt_generation_service import StarterPromptGenerationService


class PromptProposalApplyService:
    @staticmethod
    def _normalized_prompts(prompts: list[dict]) -> list[str]:
        return [
            StarterPromptGenerationService.normalize_text(item["text"])
            for item in prompts
        ]

    @classmethod
    def apply(cls, db: Session, project_id: int, proposal_id: int, prompts: list | None) -> dict:
        proposal = db.scalar(
            select(PromptSetProposal).where(
                PromptSetProposal.id == proposal_id,
                PromptSetProposal.project_id == project_id,
            ).with_for_update()
        )
        if proposal is None:
            raise HTTPException(status_code=404, detail="Prompt proposal not found.")
        existing = list(db.scalars(
            select(Prompt).where(Prompt.project_id == project_id).with_for_update()
        ).all())
        if proposal.status == "approved":
            active = [item for item in existing if item.is_active]
            expected = cls._normalized_prompts(proposal.prompts)
            actual = [StarterPromptGenerationService.normalize_text(item.text) for item in active]
            if len(actual) == len(expected) and set(actual) == set(expected):
                return {
                    "project_id": project_id,
                    "proposal_id": proposal_id,
                    "active_prompt_count": len(active),
                    "active_prompt_ids": [item.id for item in active],
                }
            raise HTTPException(
                status_code=409,
                detail="Prompt proposal was applied, but the active set has since changed.",
            )
        if proposal.status != "proposed":
            raise HTTPException(status_code=409, detail="Prompt proposal cannot be applied.")
        selected = [item.model_dump() for item in prompts] if prompts is not None else proposal.prompts
        if not selected or len(selected) > 20:
            raise HTTPException(status_code=400, detail="Select between 1 and 20 proposal prompts.")
        if any(StarterPromptGenerationService.is_near_duplicate(
            item["text"], [other["text"] for other in selected[:index]]
        ) for index, item in enumerate(selected)):
            raise HTTPException(status_code=400, detail="The edited proposal contains duplicate prompts.")
        blueprint, warnings = StarterPromptGenerationService.coverage(
            selected,
            proposal.measurement_scope,
            proposal.topic_clusters,
            proposal.coverage_blueprint.get("core_category"),
            proposal.coverage_blueprint.get("crawl_sample_bias"),
        )
        by_text = {StarterPromptGenerationService.normalize_text(item.text): item for item in existing}
        active_ids = []
        all_prompts = list(existing)
        try:
            for prompt in existing:
                prompt.is_active = False
            for item in selected:
                normalized = StarterPromptGenerationService.normalize_text(item["text"])
                prompt = by_text.get(normalized)
                if prompt is None:
                    prompt = Prompt(project_id=project_id, text=item["text"].strip(),
                                    category=item["category"], intent=item["category"], is_active=True)
                    db.add(prompt)
                    db.flush()
                    all_prompts.append(prompt)
                else:
                    prompt.is_active = True
                    prompt.category = item["category"]
                active_ids.append(prompt.id)
            if sum(bool(prompt.is_active) for prompt in all_prompts) != len(selected):
                raise RuntimeError("Prompt proposal replacement did not produce the expected active set.")
            proposal.prompts = selected
            proposal.coverage_blueprint = blueprint
            proposal.warnings = warnings
            proposal.status = "approved"
            proposal.approved_at = datetime.now(timezone.utc)
            db.commit()
        except Exception:
            db.rollback()
            raise
        return {"project_id": project_id, "proposal_id": proposal_id,
                "active_prompt_count": len(active_ids), "active_prompt_ids": active_ids}
