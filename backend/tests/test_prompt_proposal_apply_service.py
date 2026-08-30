import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.models.prompt import Prompt
from app.services.prompt_proposal_apply_service import PromptProposalApplyService
from app.services.starter_prompt_generation_service import StarterPromptGenerationService


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

    @patch.object(StarterPromptGenerationService, "coverage", return_value=({}, []))
    @patch.object(StarterPromptGenerationService, "is_near_duplicate", return_value=False)
    def test_replacing_old_19_with_new_19_leaves_exactly_19_active(
        self, _duplicate, _coverage
    ):
        selected = [
            {
                "text": f"Replacement prompt {index}",
                "category": "comparison",
                "topic_cluster": "Platform",
                "rationale": None,
            }
            for index in range(19)
        ]
        proposal = SimpleNamespace(
            id=8,
            project_id=8,
            status="proposed",
            measurement_scope="brand_wide",
            topic_clusters=[],
            coverage_blueprint={"core_category": None},
            warnings=[],
            prompts=selected,
            approved_at=None,
        )
        old_prompts = [
            Prompt(
                id=index + 1,
                project_id=8,
                text=f"Historical prompt {index}",
                category="informational",
                is_active=True,
            )
            for index in range(19)
        ]
        created = []
        db = MagicMock()
        db.scalar.return_value = proposal
        db.scalars.return_value.all.return_value = old_prompts

        def assign_id(prompt):
            prompt.id = 100 + len(created)
            created.append(prompt)

        db.add.side_effect = assign_id

        result = PromptProposalApplyService.apply(db, 8, 8, None)

        self.assertEqual(result["active_prompt_count"], 19)
        self.assertEqual(len(set(result["active_prompt_ids"])), 19)
        self.assertEqual(sum(prompt.is_active for prompt in old_prompts + created), 19)
        self.assertTrue(all(not prompt.is_active for prompt in old_prompts))
        self.assertTrue(all(prompt.is_active for prompt in created))
        self.assertEqual(len(old_prompts + created), 38)
        db.commit.assert_called_once_with()

    def test_retry_of_applied_proposal_returns_same_active_set_without_writes(self):
        selected = [
            {"text": f"Approved prompt {index}", "category": "comparison"}
            for index in range(19)
        ]
        proposal = SimpleNamespace(
            id=8,
            project_id=8,
            status="approved",
            prompts=selected,
        )
        history = [
            Prompt(
                id=index + 1,
                project_id=8,
                text=f"Historical prompt {index}",
                category="informational",
                is_active=False,
            )
            for index in range(19)
        ]
        active = [
            Prompt(
                id=100 + index,
                project_id=8,
                text=item["text"],
                category=item["category"],
                is_active=True,
            )
            for index, item in enumerate(selected)
        ]
        db = MagicMock()
        db.scalar.return_value = proposal
        db.scalars.return_value.all.return_value = history + active

        result = PromptProposalApplyService.apply(db, 8, 8, None)

        self.assertEqual(result["active_prompt_count"], 19)
        self.assertEqual(result["active_prompt_ids"], [prompt.id for prompt in active])
        db.add.assert_not_called()
        db.flush.assert_not_called()
        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
