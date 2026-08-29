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

    @staticmethod
    def broad_prompts():
        categories = [
            "brand", "informational", "problem_solution", "recommendation",
            "comparison", "commercial",
        ]
        topics = ["Gateway", "Agents", "Deployments", "Security", "Analytics", "Core Cloud"]
        return [
            {"text": f"Unbranded question {index} about {topic}", "topic_cluster": topic, "category": category}
            for index, (topic, category) in enumerate(zip(topics, categories), start=1)
        ]

    def test_small_clusters_in_one_macro_family_trigger_family_guard(self):
        prompts = self.broad_prompts()
        clusters = [
            {"name": "Gateway", "topic_family": "AI Platform", "is_major_family": True},
            {"name": "Agents", "topic_family": "AI Platform", "is_major_family": True},
            {"name": "Deployments", "topic_family": "AI Platform", "is_major_family": True},
            {"name": "Security", "topic_family": "Trust", "is_major_family": True},
            {"name": "Analytics", "topic_family": "Observability", "is_major_family": True},
            {"name": "Core Cloud", "topic_family": "Cloud Platform", "is_major_family": True},
        ]
        core = {"name": "Cloud Platform", "topic_family": "Cloud Platform", "target_terms": ["Example"]}

        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide", clusters, core)

        self.assertEqual(blueprint["largest_topic_share"], round(1 / 6, 4))
        self.assertEqual(blueprint["largest_topic_family_share"], 0.5)
        self.assertEqual(blueprint["concentration_status"], "needs_review")
        self.assertTrue(any("AI Platform" in warning and "50%" in warning for warning in warnings))

    def test_brand_wide_checklist_requires_core_and_unbranded_discovery(self):
        prompts = self.broad_prompts()
        clusters = [
            {"name": topic, "topic_family": family, "is_major_family": True}
            for topic, family in zip(
                ["Gateway", "Agents", "Deployments", "Security", "Analytics", "Core Cloud"],
                ["AI", "Automation", "Deployment", "Trust", "Observability", "Cloud Platform"],
            )
        ]
        core = {"name": "Cloud Platform", "topic_family": "Cloud Platform", "target_terms": ["Example"]}

        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide", clusters, core)

        self.assertTrue(all(blueprint["brand_wide_checklist"].values()))
        self.assertEqual(blueprint["concentration_status"], "balanced")
        self.assertEqual(warnings, [])

    def test_brand_wide_distribution_is_not_forced_to_be_equal(self):
        prompts = self.broad_prompts() + [
            {"text": "Another deployment question", "topic_cluster": "Deployments", "category": "informational"}
        ]
        clusters = [
            {"name": topic, "topic_family": family, "is_major_family": True}
            for topic, family in zip(
                ["Gateway", "Agents", "Deployments", "Security", "Analytics", "Core Cloud"],
                ["AI", "Automation", "Deployment", "Trust", "Observability", "Cloud Platform"],
            )
        ]
        core = {"name": "Cloud Platform", "topic_family": "Cloud Platform", "target_terms": ["Example"]}

        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide", clusters, core)

        self.assertEqual(blueprint["topic_family_distribution"]["Deployment"], 2)
        self.assertEqual(blueprint["concentration_status"], "balanced")
        self.assertEqual(warnings, [])

    def test_focused_scope_is_exempt_from_macro_broadness_guard(self):
        prompts = [
            {"text": f"Focused question {index}", "topic_cluster": "Payments", "category": category}
            for index, category in enumerate(StarterPromptGenerationService.REQUIRED_INTENTS, start=1)
        ]
        clusters = [{"name": "Payments", "topic_family": "Payments", "is_major_family": True}]

        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "focused", clusters, None)

        self.assertEqual(blueprint["largest_topic_family_share"], 1.0)
        self.assertEqual(blueprint["concentration_status"], "focused")
        self.assertEqual(warnings, [])

    def test_legacy_proposal_provenance_remains_readable(self):
        proposal = SimpleNamespace(
            id=1, project_id=2, status="proposed", generator_version="balanced-v2",
            measurement_scope="brand_wide", focus_label=None, model_name="Model",
            source_page_count=4,
            topic_clusters=[{"name": "Deployment", "evidence": ["deploy"], "allocated_prompts": 1}],
            coverage_blueprint={"topic_distribution": {"Deployment": 1}, "intent_distribution": {"brand": 1}, "largest_topic_share": 1.0, "concentration_status": "needs_review"},
            prompts=[{"text": "What is Example?", "category": "brand", "topic_cluster": "Deployment", "rationale": None}],
            warnings=[], created_at=None,
        )

        result = StarterPromptGenerationService._serialize(proposal)

        self.assertEqual(result["topic_clusters"][0]["topic_family"], "Deployment")
        self.assertEqual(result["coverage_blueprint"]["largest_topic_family_share"], 1.0)


if __name__ == "__main__":
    unittest.main()
