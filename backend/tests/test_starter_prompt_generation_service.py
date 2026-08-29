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

    def test_homepage_and_top_level_evidence_are_prioritized_over_deep_pages(self):
        pages = [
            SimpleNamespace(url="https://example.com/", title="Core market", h1="Core platform"),
            SimpleNamespace(url="https://example.com/products", title="Products", h1="Product areas"),
            SimpleNamespace(url="https://example.com/docs/ai/agents/tutorial", title="Agent tutorial", h1="Agents"),
        ]

        tiers = StarterPromptGenerationService.evidence_tiers(pages)

        self.assertEqual([page.url for page in tiers["homepage"]], ["https://example.com/"])
        self.assertEqual([page.url for page in tiers["top_level"]], ["https://example.com/products"])
        self.assertEqual([page.url for page in tiers["broader_corpus"]], ["https://example.com/docs/ai/agents/tutorial"])

    def test_biased_deep_crawl_is_detected_against_stronger_evidence(self):
        pages = [
            SimpleNamespace(url="https://example.com/", title="Application platform", h1="Deploy applications"),
            SimpleNamespace(url="https://example.com/products", title="Cloud products", h1="Platform products"),
        ] + [
            SimpleNamespace(url=f"https://example.com/docs/agents/{index}", title="Agent runtime", h1="Agent tools")
            for index in range(6)
        ]

        result = StarterPromptGenerationService.crawl_sample_bias_signal(pages)

        self.assertTrue(result["detected"])
        self.assertIn("deeper pages", result["reason"])
        self.assertGreaterEqual(len(result["evidence"]), 1)

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

        self.assertEqual(round(max(blueprint["provider_topic_distribution"].values()) / 6, 4), round(1 / 6, 4))
        self.assertEqual(blueprint["largest_topic_family_share"], 0.5)
        self.assertEqual(blueprint["concentration_status"], "needs_review")
        self.assertTrue(any("AI and agent infrastructure" in warning and "50%" in warning for warning in warnings))

    def test_two_families_in_one_super_theme_trigger_super_theme_guard(self):
        prompts = self.broad_prompts()
        clusters = [
            {"name": "Gateway", "topic_family": "AI Apps", "super_theme": "AI Ecosystem", "is_major_family": True, "is_major_super_theme": True},
            {"name": "Agents", "topic_family": "Agent Runtime", "super_theme": "AI Ecosystem", "is_major_family": True, "is_major_super_theme": True},
            {"name": "Deployments", "topic_family": "Deploy", "super_theme": "Web Platform", "is_major_family": True, "is_major_super_theme": True},
            {"name": "Security", "topic_family": "Trust", "super_theme": "Trust", "is_major_family": True, "is_major_super_theme": True},
            {"name": "Analytics", "topic_family": "Observe", "super_theme": "Operations", "is_major_family": True, "is_major_super_theme": True},
            {"name": "Core Cloud", "topic_family": "Cloud", "super_theme": "Cloud", "is_major_family": True, "is_major_super_theme": True},
        ]
        core = {"name": "Cloud", "topic_family": "Cloud", "super_theme": "Cloud", "target_terms": ["Example"], "market_structure": "multi_theme"}

        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide", clusters, core)

        self.assertEqual(round(max(blueprint["provider_topic_family_distribution"].values()) / 6, 4), round(1 / 6, 4))
        self.assertEqual(blueprint["largest_super_theme_share"], round(2 / 6, 4))
        self.assertFalse(any("super-theme guard" in warning for warning in warnings))

        for cluster in clusters[:3]:
            cluster["super_theme"] = "AI Ecosystem"
        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide", clusters, core)
        self.assertEqual(blueprint["largest_super_theme_share"], 0.5)
        self.assertTrue(any("AI / Agent Ecosystem" in warning and "50%" in warning for warning in warnings))

    def test_renaming_related_clusters_does_not_evade_super_theme_guard(self):
        prompts = [
            {"text": f"Question {index}", "topic_cluster": name, "category": category}
            for index, (name, category) in enumerate(zip(
                ["AI One", "AI Two", "AI Three", "Core", "Trust", "Ops"],
                ["brand", "informational", "problem_solution", "recommendation", "comparison", "commercial"],
            ))
        ]
        clusters = [
            {"name": name, "topic_family": name, "super_theme": "AI Ecosystem" if name.startswith("AI") else name,
             "is_major_family": True, "is_major_super_theme": True}
            for name in ["AI One", "AI Two", "AI Three", "Core", "Trust", "Ops"]
        ]
        core = {"name": "Core", "topic_family": "Core", "super_theme": "Core", "target_terms": ["Example"], "market_structure": "multi_theme"}

        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide", clusters, core)

        self.assertEqual(round(max(blueprint["provider_topic_distribution"].values()) / 6, 4), round(1 / 6, 4))
        self.assertEqual(round(max(blueprint["provider_topic_family_distribution"].values()) / 6, 4), round(1 / 6, 4))
        self.assertEqual(blueprint["largest_super_theme_share"], 0.5)
        self.assertTrue(any("super-theme guard" in warning for warning in warnings))

    def test_ai_and_agent_super_theme_labels_are_semantically_grouped(self):
        prompts = self.broad_prompts()
        clusters = [
            {"name": "Gateway", "topic_family": "AI Platform", "super_theme": "AI application development", "is_major_family": True, "is_major_super_theme": True},
            {"name": "Agents", "topic_family": "Agents", "super_theme": "Agentic infrastructure", "is_major_family": True, "is_major_super_theme": True},
            {"name": "Deployments", "topic_family": "Deploy", "super_theme": "Web delivery", "is_major_family": True, "is_major_super_theme": True},
            {"name": "Security", "topic_family": "Trust", "super_theme": "Trust", "is_major_family": True, "is_major_super_theme": True},
            {"name": "Analytics", "topic_family": "Observe", "super_theme": "Operations", "is_major_family": True, "is_major_super_theme": True},
            {"name": "Core Cloud", "topic_family": "Cloud", "super_theme": "Cloud", "is_major_family": True, "is_major_super_theme": True},
        ]
        core = {"name": "Cloud", "topic_family": "Cloud", "super_theme": "Cloud",
                "target_terms": ["Example"], "market_structure": "multi_theme"}

        blueprint, _warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide", clusters, core)

        grouped_name = next(name for name in blueprint["super_theme_distribution"] if "AI / Agent" in name)
        self.assertEqual(blueprint["super_theme_distribution"][grouped_name], 2)

    def test_genuinely_single_theme_brand_can_justify_dominance(self):
        prompts = [
            {"text": f"Payments question {index}", "topic_cluster": topic, "category": category}
            for index, (topic, category) in enumerate(zip(
                ["Gateway", "Agents", "Deployments", "Security", "Analytics", "Core Cloud"],
                ["brand", "informational", "problem_solution", "recommendation", "comparison", "commercial"],
            ))
        ]
        clusters = [
            {"name": topic, "topic_family": topic, "super_theme": "Payments",
             "is_major_family": True, "is_major_super_theme": True, "dominance_justified": True}
            for topic in ["Gateway", "Agents", "Deployments", "Security", "Analytics", "Core Cloud"]
        ]
        core = {"name": "Payments", "topic_family": "Gateway", "super_theme": "Payments",
                "target_terms": ["Example"], "market_structure": "single_theme"}

        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide", clusters, core)

        self.assertEqual(blueprint["largest_super_theme_share"], 1.0)
        self.assertFalse(any("super-theme guard" in warning for warning in warnings))

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

    def test_crawl_sample_bias_is_preserved_as_structured_provenance(self):
        prompts = self.broad_prompts()
        clusters = [
            {"name": topic, "topic_family": family, "super_theme": family,
             "is_major_family": True, "is_major_super_theme": True}
            for topic, family in zip(
                ["Gateway", "Agents", "Deployments", "Security", "Analytics", "Core Cloud"],
                ["AI", "Automation", "Deployment", "Trust", "Observability", "Cloud Platform"],
            )
        ]
        core = {"name": "Cloud Platform", "topic_family": "Cloud Platform",
                "super_theme": "Cloud Platform", "target_terms": ["Example"]}
        bias = {"detected": True, "reason": "Deep pages overrepresent one product area.",
                "evidence": ["https://example.com/"]}

        blueprint, _warnings = StarterPromptGenerationService.coverage(
            prompts, "brand_wide", clusters, core, bias
        )

        self.assertTrue(blueprint["crawl_sample_bias"]["detected"])
        self.assertIn("Deep pages", blueprint["crawl_sample_bias"]["reason"])

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

    @staticmethod
    def repair_fixture(ai_count=14, include_commercial=True):
        categories = ["brand", "informational", "problem_solution", "recommendation", "comparison"]
        if include_commercial:
            categories.append("commercial")
        prompts = []
        ai_topics = ["AI Runtime", "AI Gateway", "Agent Tools", "Model Access"]
        web_topics = ["Web Delivery", "Developer Workflow"]
        trust_topics = ["Security", "Observability"]
        remaining = 19 - ai_count
        web_count = (remaining + 1) // 2
        for index in range(19):
            if index < ai_count:
                topic = ai_topics[index % len(ai_topics)]
            elif index < ai_count + web_count:
                topic = web_topics[(index - ai_count) % len(web_topics)]
            else:
                topic = trust_topics[(index - ai_count - web_count) % len(trust_topics)]
            prompts.append({
                "text": f"Useful question {index} about {topic}",
                "topic_cluster": topic,
                "category": categories[index % len(categories)],
                "rationale": None,
            })
        clusters = [
            {"name": name, "topic_family": "Agent Runtime" if index < 2 else "AI Services",
             "super_theme": "AI Ecosystem", "is_major_family": True, "is_major_super_theme": True}
            for index, name in enumerate(ai_topics)
        ] + [
            {"name": name, "topic_family": "Application Delivery",
             "super_theme": "Web Platform", "is_major_family": True, "is_major_super_theme": True}
            for index, name in enumerate(web_topics)
        ] + [
            {"name": name, "topic_family": name, "super_theme": "Trust and Operations",
             "is_major_family": True, "is_major_super_theme": True}
            for name in trust_topics
        ]
        core = {"name": "Application Platform", "topic_family": "Application Delivery",
                "super_theme": "Web Platform", "target_terms": ["Example"], "market_structure": "multi_theme"}
        return prompts, clusters, core

    def test_balanced_initial_proposal_does_not_create_repair_brief(self):
        prompts, clusters, core = self.repair_fixture(ai_count=7)
        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide", clusters, core)

        brief = StarterPromptGenerationService.build_repair_brief(prompts, clusters, blueprint, warnings)

        self.assertEqual(blueprint["concentration_status"], "balanced")
        self.assertIsNone(brief)

    def test_related_ai_family_dominance_creates_deterministic_repair_brief(self):
        prompts, clusters, core = self.repair_fixture()
        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide", clusters, core)

        first = StarterPromptGenerationService.build_repair_brief(prompts, clusters, blueprint, warnings)
        second = StarterPromptGenerationService.build_repair_brief(prompts, clusters, blueprint, warnings)

        self.assertEqual(first, second)
        self.assertEqual(first["replacement_count"], 7)
        self.assertEqual(first["retained_count"], 12)
        self.assertEqual(first["overrepresented_themes"][0]["count"], 14)
        self.assertEqual(first["overrepresented_themes"][0]["limit"], 0.45)
        self.assertTrue(all(item["topic_cluster"] in {"AI Runtime", "AI Gateway", "Agent Tools", "Model Access"}
                            for item in first["replacement_candidates"]))

    def test_missing_commercial_intent_is_a_repair_deficit(self):
        prompts, clusters, core = self.repair_fixture(ai_count=8, include_commercial=False)
        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide", clusters, core)

        brief = StarterPromptGenerationService.build_repair_brief(prompts, clusters, blueprint, warnings)

        self.assertIn("commercial", brief["missing_intents"])
        self.assertGreaterEqual(brief["replacement_count"], 1)

    def test_focused_and_evidence_justified_single_theme_sets_do_not_repair(self):
        prompts, clusters, _core = self.repair_fixture(ai_count=19)
        focused_blueprint, focused_warnings = StarterPromptGenerationService.coverage(
            prompts, "focused", clusters, None
        )
        single_topics = ["Payments", "Billing", "Invoices", "Collections", "Revenue", "Reporting"]
        single_prompts = [
            {"text": f"Single market question {index}", "topic_cluster": single_topics[index % 6],
             "category": list(StarterPromptGenerationService.REQUIRED_INTENTS)[index % 6], "rationale": None}
            for index in range(18)
        ]
        single_theme_clusters = [
            {"name": name, "topic_family": name, "super_theme": "Payments",
             "is_major_family": True, "is_major_super_theme": True, "dominance_justified": True}
            for name in single_topics
        ]
        core = {"name": "Payments", "topic_family": "Payments", "super_theme": "Payments",
                "target_terms": ["Example"], "market_structure": "single_theme"}
        single_blueprint, single_warnings = StarterPromptGenerationService.coverage(
            single_prompts, "brand_wide", single_theme_clusters, core
        )

        self.assertIsNone(StarterPromptGenerationService.build_repair_brief(
            prompts, clusters, focused_blueprint, focused_warnings
        ))
        self.assertIsNone(StarterPromptGenerationService.build_repair_brief(
            single_prompts, single_theme_clusters, single_blueprint, single_warnings
        ))

    def test_repaired_result_remains_needs_review_when_still_over_limit(self):
        prompts, clusters, core = self.repair_fixture(ai_count=10)

        blueprint, warnings = StarterPromptGenerationService.coverage(prompts, "brand_wide", clusters, core)

        self.assertEqual(blueprint["concentration_status"], "needs_review")
        self.assertTrue(any("super-theme guard" in warning for warning in warnings))

    def test_prompt_meaning_overrides_generic_provider_connectivity_label(self):
        classification = StarterPromptGenerationService.semantic_prompt_classification(
            {"text": "How should an AI application connect to external services?", "topic_cluster": "Connectivity"},
            {"name": "Connectivity", "topic_family": "Web Platform", "super_theme": "Web Delivery"},
        )

        self.assertEqual(classification["effective_super_theme"], "AI / Agent Ecosystem")
        self.assertEqual(classification["effective_micro_cluster"], "AI application integration")
        self.assertTrue(classification["reclassified"])

    def test_mixed_prompt_records_secondary_theme_without_fractional_math(self):
        classification = StarterPromptGenerationService.semantic_prompt_classification(
            {"text": "How can an AI application improve payment processing?", "topic_cluster": "Applications"},
            {"name": "Applications", "topic_family": "Software", "super_theme": "Application Platform"},
        )

        self.assertEqual(classification["effective_super_theme"], "Payments Ecosystem")
        self.assertIn("AI / Agent Ecosystem", classification["secondary_themes"])

    def test_payment_and_crm_prompts_group_generically_from_text(self):
        payment = StarterPromptGenerationService.semantic_prompt_classification(
            {"text": "How should merchants compare checkout and payment fraud controls?", "topic_cluster": "Risk"},
            {"name": "Risk", "topic_family": "Commerce", "super_theme": "Business Software"},
        )
        crm = StarterPromptGenerationService.semantic_prompt_classification(
            {"text": "Which CRM automation supports lead nurturing and a sales pipeline?", "topic_cluster": "Automation"},
            {"name": "Automation", "topic_family": "Software", "super_theme": "Business Software"},
        )

        self.assertEqual(payment["effective_super_theme"], "Payments Ecosystem")
        self.assertEqual(crm["effective_super_theme"], "Marketing / CRM Ecosystem")

    def test_core_brand_market_is_separate_from_strategic_emphasis(self):
        prompts, clusters, core = self.repair_fixture(ai_count=10)
        core["name"] = "Current AI Initiative"
        core["topic_family"] = "Agent Runtime"
        core["super_theme"] = "AI Ecosystem"

        blueprint, _warnings = StarterPromptGenerationService.coverage(
            prompts, "brand_wide", clusters, core
        )

        self.assertEqual(blueprint["core_category"]["strategic_emphasis"]["name"], "Current AI Initiative")
        self.assertEqual(blueprint["core_category"]["core_brand_market"]["name"], "Application Delivery")

    def test_semantic_reclassification_drives_repair_brief(self):
        prompts, clusters, core = self.repair_fixture(ai_count=7)
        for index in range(4):
            prompts[7 + index]["text"] = f"How should AI application integration scenario {index} work?"
        blueprint, warnings = StarterPromptGenerationService.coverage(
            prompts, "brand_wide", clusters, core
        )
        brief = StarterPromptGenerationService.build_repair_brief(
            prompts, clusters, blueprint, warnings
        )

        self.assertEqual(blueprint["concentration_status"], "needs_review")
        self.assertEqual(blueprint["super_theme_distribution"]["AI / Agent Ecosystem"], 11)
        self.assertIsNotNone(brief)
        self.assertEqual(brief["overrepresented_themes"][0]["name"], "AI / Agent Ecosystem")

    def test_repair_rejects_reordered_replacement_candidates(self):
        retained = [{"text": "Keep this prompt"}]
        candidates = [{"text": "Replace this prompt"}]
        reordered = [{"text": "Replace this prompt"}, {"text": "Keep this prompt"}]

        with self.assertRaisesRegex(ValueError, "relabelled or reordered"):
            StarterPromptGenerationService.validate_repair_text_changes(
                reordered,
                {"retained_prompts": retained, "replacement_candidates": candidates},
            )

    def test_repair_accepts_genuinely_broader_replacement_text(self):
        retained = [{"text": "Keep this prompt"}]
        candidates = [{"text": "Replace this AI prompt"}]
        repaired = [{"text": "Keep this prompt"}, {"text": "Broader deployment prompt"}]

        counts = StarterPromptGenerationService.validate_repair_text_changes(
            repaired,
            {"retained_prompts": retained, "replacement_candidates": candidates},
        )

        self.assertEqual(counts, (1, 1))


if __name__ == "__main__":
    unittest.main()
