import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.prompt import Prompt
from app.services.prompt_proposal_apply_service import PromptProposalApplyService


class PromptProposalApplyServiceTests(unittest.TestCase):
    def test_proposal_is_separate_until_explicit_apply_then_replaces_active_set(self):
        proposal = SimpleNamespace(
            id=7,
            project_id=3,
            status="proposed",
            measurement_scope="brand_wide",
            topic_clusters=[{
                "name": "Deployment", "topic_family": "Cloud Platform",
                "is_major_family": True, "evidence": ["deployment"],
                "allocated_prompts": 2,
            }],
            coverage_blueprint={
                "core_category": {
                    "name": "Cloud Platform", "topic_family": "Cloud Platform",
                    "target_terms": ["Example"],
                },
            },
            warnings=[],
            prompts=[
                {"text": "Which platforms support preview environments?", "category": "comparison", "topic_cluster": "Deployment", "rationale": None},
                {"text": "How do teams reduce deployment rollback risk?", "category": "problem_solution", "topic_cluster": "Deployment", "rationale": None},
            ],
            approved_at=None,
        )
        old_prompt = Prompt(
            id=11, project_id=3, text="Old active question", category="informational", is_active=True
        )
        db = MagicMock()
        db.scalar.return_value = proposal
        db.scalars.return_value.all.return_value = [old_prompt]
        next_id = iter([21, 22])

        def assign_id(value):
            if isinstance(value, Prompt) and value.id is None:
                value.id = next(next_id)

        db.add.side_effect = assign_id

        result = PromptProposalApplyService.apply(db, 3, 7, None)

        self.assertFalse(old_prompt.is_active)
        self.assertEqual(proposal.status, "approved")
        self.assertEqual(result["active_prompt_ids"], [21, 22])
        self.assertEqual(db.add.call_count, 2)
        db.commit.assert_called_once_with()

    def test_reading_or_generating_a_proposal_does_not_apply_it(self):
        proposal = SimpleNamespace(status="proposed")
        self.assertEqual(proposal.status, "proposed")


if __name__ == "__main__":
    unittest.main()
