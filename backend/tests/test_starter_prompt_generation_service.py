import unittest
from types import SimpleNamespace

from app.schemas.starter_prompt_generation import StarterPromptGenerateRequest
from app.services.starter_prompt_generation_service import StarterPromptGenerationService


class StarterPromptGenerationServiceTests(unittest.TestCase):
    def test_existing_projects_default_to_brand_wide_scope(self):
        request = StarterPromptGenerateRequest()
        self.assertEqual(request.measurement_scope, "brand_wide")
        self.assertIsNone(request.focus_label)

    def test_focused_scope_requires_an_explicit_focus(self):
        with self.assertRaises(ValueError):
            StarterPromptGenerateRequest(measurement_scope="focused")
        request = StarterPromptGenerateRequest(
            measurement_scope="focused", focus_label="Payments"
        )
        self.assertEqual(request.focus_label, "Payments")

    def test_topic_terms_are_derived_from_project_page_evidence(self):
        pages = [
            SimpleNamespace(url="https://example.com/payments/invoicing", title="Automated Invoicing", h1="Billing workflows"),
            SimpleNamespace(url="https://example.com/payments", title="Payment orchestration", h1="Global payments"),
        ]
        terms = StarterPromptGenerationService.evidence_terms(pages)
        self.assertIn("payments", terms)
        self.assertIn("invoicing", terms)
        self.assertNotIn("unrelated", terms)

    def test_brand_wide_concentration_and_missing_intents_need_review(self):
        prompts = [
            {"topic_cluster": "AI", "category": "informational"},
            {"topic_cluster": "AI", "category": "commercial"},
            {"topic_cluster": "AI", "category": "brand"},
            {"topic_cluster": "Hosting", "category": "comparison"},
        ]
        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide")
        self.assertEqual(blueprint["concentration_status"], "needs_review")
        self.assertEqual(blueprint["largest_topic_share"], 0.75)
        self.assertTrue(any("35%" in warning for warning in warnings))
        self.assertTrue(any("recommendation" in warning for warning in warnings))

    def test_focused_scope_may_legitimately_concentrate(self):
        prompts = [
            {"topic_cluster": "Payments", "category": category}
            for category in StarterPromptGenerationService.REQUIRED_INTENTS
        ]
        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "focused")
        self.assertEqual(blueprint["concentration_status"], "focused")
        self.assertEqual(warnings, [])

    def test_near_duplicate_prompts_are_rejected(self):
        self.assertTrue(StarterPromptGenerationService.is_near_duplicate(
            "What are the best deployment platforms for teams?",
            ["What are the best deployment platforms for a team?"],
        ))
        self.assertFalse(StarterPromptGenerationService.is_near_duplicate(
            "How do edge functions reduce request latency?",
            ["Which deployment platforms support preview environments?"],
        ))


if __name__ == "__main__":
    unittest.main()
