import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.schemas.starter_prompt_generation import StarterPromptSuggestion
from app.services.starter_prompt_generation_service import StarterPromptGenerationService


class PromptProposalEditServiceTests(unittest.TestCase):
    def proposal(self, status="proposed"):
        return SimpleNamespace(
            id=12,
            project_id=8,
            status=status,
            generator_version=StarterPromptGenerationService.GENERATOR_VERSION,
            measurement_scope="brand_wide",
            focus_label=None,
            model_name="Stored generator model",
            source_page_count=1,
            topic_clusters=[{
                "name": "AI Platforms",
                "topic_family": "AI Platforms",
                "super_theme": "AI / Agent Ecosystem",
                "evidence": ["ai"],
                "is_major_family": True,
                "is_major_super_theme": True,
                "dominance_justified": False,
                "allocated_prompts": 2,
            }],
            coverage_blueprint={
                "core_category": None,
                "crawl_sample_bias": {"detected": False, "reason": None, "evidence": []},
                "super_theme_distribution": {"AI / Agent Ecosystem": 2},
            },
            warnings=["stale warning"],
            prompts=[
                {"text": "Which AI agent platforms should teams evaluate?", "category": "recommendation", "topic_cluster": "AI Platforms", "rationale": None},
                {"text": "How does Vercel support AI agents?", "category": "brand", "topic_cluster": "AI Platforms", "rationale": None},
            ],
            created_at=datetime.now(timezone.utc),
        )

    def test_edit_persists_only_proposal_and_recalculates_semantic_coverage(self):
        proposal = self.proposal()
        db = MagicMock()
        db.scalar.return_value = proposal
        edited = [
            StarterPromptSuggestion(
                text="How do preview deployments improve application delivery?",
                category="informational",
                topic_cluster="AI Platforms",
            ),
            StarterPromptSuggestion(**proposal.prompts[1]),
        ]

        result = StarterPromptGenerationService.update_proposal(db, 8, 12, edited)

        self.assertEqual(proposal.prompts[0]["text"], edited[0].text)
        self.assertEqual(result["prompts"], proposal.prompts)
        self.assertEqual(
            result["coverage_blueprint"]["manual_revalidation"]["coverage_status"],
            result["coverage_blueprint"]["concentration_status"],
        )
        self.assertEqual(
            result["coverage_blueprint"]["intent_distribution"],
            {"informational": 1, "brand": 1},
        )
        self.assertEqual(len(result["coverage_blueprint"]["effective_classifications"]), 2)
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(proposal)
        db.add.assert_not_called()

    def test_applied_proposal_cannot_be_edited(self):
        db = MagicMock()
        db.scalar.return_value = self.proposal(status="approved")

        with self.assertRaises(HTTPException) as context:
            StarterPromptGenerationService.update_proposal(db, 8, 12, [])

        self.assertEqual(context.exception.status_code, 409)
        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
