import unittest

from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.project_readiness_service import (
    ProjectReadinessService,
)


class ProjectReadinessServiceTests(unittest.TestCase):

    def setUp(self):
        self.db = Mock()
        self.project = SimpleNamespace(
            id=5,
            name="Validation",
        )
        self.target = SimpleNamespace(
            id=28,
            name="Example",
        )
        self.website = SimpleNamespace(
            id=17,
            brand_id=28,
            domain="example.com",
            base_url="https://example.com/",
            is_primary=True,
            last_crawl_summary=None,
        )
        self.prompts = [
            SimpleNamespace(
                id=1,
                text="What is Example?",
                category="brand",
                is_active=True,
            ),
            SimpleNamespace(
                id=2,
                text="Compare Example products",
                category="comparison",
                is_active=True,
            ),
        ]
        self.competitor = SimpleNamespace(
            id=29,
            name="Alternative",
        )

    def build(
        self,
        *,
        websites=None,
        prompts=None,
        pages=None,
        brand_roles=None,
        historical_modes=None,
        first_party_suggestions=None,
        pending_competitor_suggestions=0,
    ):
        with ExitStack() as stack:
            stack.enter_context(patch(
                "app.services.project_readiness_service.ProjectRepository.get_by_id",
                return_value=self.project,
            ))
            stack.enter_context(patch(
                "app.services.project_readiness_service.ProjectBrandRepository.list_brand_roles",
                return_value=brand_roles if brand_roles is not None else [
                    (self.target, "target"),
                    (self.competitor, "competitor"),
                ],
            ))
            stack.enter_context(patch(
                "app.services.project_readiness_service.WebsiteRepository.list_by_brand",
                return_value=websites if websites is not None else [self.website],
            ))
            stack.enter_context(patch(
                "app.services.project_readiness_service.PromptRepository.list_by_project",
                return_value=prompts if prompts is not None else self.prompts,
            ))
            stack.enter_context(patch(
                "app.services.project_readiness_service.PageRepository.list_by_website",
                return_value=pages if pages is not None else [],
            ))
            stack.enter_context(patch(
                "app.services.project_readiness_service.TechnicalAuditRepository.get_latest",
                return_value=None,
            ))
            stack.enter_context(patch(
                "app.services.project_readiness_service.AIModelService.resolve_execution_model",
                return_value=SimpleNamespace(
                    provider_model_id="gpt-test",
                ),
            ))
            stack.enter_context(patch.object(
                ProjectReadinessService,
                "_historical_modes",
                return_value=historical_modes or set(),
            ))
            stack.enter_context(patch.object(
                ProjectReadinessService,
                "_first_party_suggestions",
                return_value=first_party_suggestions or [],
            ))
            stack.enter_context(patch.object(
                ProjectReadinessService,
                "_competitor_suggestions",
                return_value=[],
            ))
            stack.enter_context(patch(
                "app.services.project_readiness_service."
                "CompetitorDiscoveryRepository.pending_count",
                return_value=pending_competitor_suggestions,
            ))
            return ProjectReadinessService.build(
                self.db,
                self.project.id,
            )

    def test_robots_blocked_crawl_limits_technical_and_blocks_site_rag(self):
        self.website.last_crawl_summary = {
            "pages_blocked_by_robots": 1,
            "pages_crawled": 0,
            "crawl_limited": True,
        }

        result = self.build()

        self.assertEqual(
            result["measurements"]["technical_seo"]["state"],
            "limited",
        )
        self.assertEqual(
            result["measurements"]["site_rag"]["state"],
            "blocked",
        )
        self.assertIn(
            "does not imply",
            result["measurements"]["technical_seo"][
                "recommended_action"
            ],
        )

    def test_healthy_corpus_makes_site_rag_ready(self):
        pages = [
            SimpleNamespace(
                status_code=200,
                content_text="useful content",
                word_count=250,
                canonical_url=None,
            )
            for _index in range(3)
        ]

        result = self.build(pages=pages)

        self.assertEqual(
            result["measurements"]["site_rag"]["state"],
            "ready",
        )
        self.assertEqual(
            result["configuration"]["usable_page_count"],
            3,
        )

    def test_single_page_is_runnable_with_limited_coverage_warning(self):
        page = SimpleNamespace(
            status_code=200,
            content_text="useful content",
            word_count=250,
            canonical_url=None,
        )

        result = self.build(pages=[page])

        technical = result["measurements"]["technical_seo"]
        self.assertEqual(technical["state"], "ready")
        self.assertTrue(technical["execution_available"])
        self.assertIn(
            "limited_technical_sample",
            [item["code"] for item in technical["warnings"]],
        )

    def test_missing_primary_website_blocks_web_site_and_technical_independently(self):
        result = self.build(websites=[])

        self.assertEqual(
            result["measurements"]["technical_seo"]["state"],
            "blocked",
        )
        self.assertEqual(
            result["measurements"]["web_search"]["state"],
            "blocked",
        )
        self.assertNotEqual(
            result["measurements"]["memory"]["state"],
            "blocked",
        )

    def test_no_active_prompts_blocks_ai_modes_but_not_technical(self):
        result = self.build(prompts=[])

        self.assertEqual(
            result["measurements"]["memory"]["state"],
            "blocked",
        )
        self.assertEqual(
            result["measurements"]["web_search"]["state"],
            "blocked",
        )
        self.assertEqual(
            result["measurements"]["site_rag"]["state"],
            "blocked",
        )
        self.assertNotEqual(
            result["measurements"]["technical_seo"]["state"],
            "blocked",
        )

    def test_suggestions_require_approval_and_get_is_read_only(self):
        suggestion = {
            "key": "first-party:example.net",
            "kind": "first_party_domain",
            "value": "example.net",
            "reason": "Stored evidence points to this domain.",
            "evidence": ["2 resolved sources."],
            "approval_required": True,
        }

        result = self.build(
            first_party_suggestions=[suggestion],
        )

        found = next(
            item for item in result["suggestions"]
            if item["key"] == suggestion["key"]
        )
        self.assertTrue(found["approval_required"])
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()
        self.db.flush.assert_not_called()

    def test_historical_results_remain_visible_when_future_site_rag_is_blocked(self):
        result = self.build(
            historical_modes={"site_rag"},
        )

        site_rag = result["measurements"]["site_rag"]
        self.assertEqual(site_rag["state"], "blocked")
        self.assertTrue(site_rag["has_historical_results"])

    def test_no_competitors_is_review_not_global_block(self):
        result = self.build(
            brand_roles=[(self.target, "target")],
        )

        self.assertEqual(
            result["measurements"]["memory"]["state"],
            "needs_review",
        )
        self.assertEqual(
            result["measurements"]["web_search"]["state"],
            "needs_review",
        )
        self.assertIn(
            "no_competitors",
            [item["code"] for item in result["warnings"]],
        )

    def test_readiness_distinguishes_pending_from_configured_competitors(self):
        result = self.build(
            brand_roles=[(self.target, "target")],
            pending_competitor_suggestions=5,
        )

        self.assertEqual(result["configuration"]["competitor_count"], 0)
        self.assertEqual(
            result["configuration"]["pending_competitor_suggestion_count"],
            5,
        )


if __name__ == "__main__":
    unittest.main()
