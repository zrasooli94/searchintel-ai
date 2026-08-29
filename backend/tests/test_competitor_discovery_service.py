import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from app.models.competitor_discovery_suggestion import CompetitorDiscoverySuggestion
from app.services.competitor_discovery_service import CompetitorDiscoveryService


class CompetitorDiscoveryServiceTests(unittest.TestCase):

    def setUp(self):
        self.db = Mock()
        self.next_id = 100

        def add(item):
            if isinstance(item, CompetitorDiscoverySuggestion):
                item.id = self.next_id
                self.next_id += 1
        self.db.add.side_effect = add
        self.db.refresh.side_effect = lambda item: None
        self.project = SimpleNamespace(id=8, name="Vercel")
        self.target = SimpleNamespace(id=54, name="Vercel")
        self.existing = SimpleNamespace(id=55, name="Existing Cloud")
        self.website = SimpleNamespace(
            id=44,
            domain="vercel.com",
            base_url="https://vercel.com/",
            is_primary=True,
        )
        self.pages = [
            SimpleNamespace(
                url="https://vercel.com/docs",
                title="Vercel Documentation",
                content_text="Deploy web applications and frontend infrastructure.",
                content_hash="abc",
                word_count=200,
            )
        ]
        self.model = SimpleNamespace(
            id=1,
            name="Test model",
            provider_model_id="test-model",
            engine_id=2,
        )
        self.engine = SimpleNamespace(id=2, slug="openai")

    def patches(self, response, *, existing_roles=None, by_domain=None):
        provider = Mock()
        provider.execute.return_value = SimpleNamespace(
            response_text=json.dumps(response),
        )
        return [
            patch("app.services.competitor_discovery_service.ProjectRepository.get_by_id", return_value=self.project),
            patch("app.services.competitor_discovery_service.ProjectBrandRepository.list_brand_roles", return_value=existing_roles or [(self.target, "target"), (self.existing, "competitor")]),
            patch("app.services.competitor_discovery_service.ProjectBrandRepository.find_identity_match", return_value=None),
            patch("app.services.competitor_discovery_service.WebsiteRepository.list_by_brand", side_effect=lambda _db, brand_id: [self.website] if brand_id == self.target.id else [SimpleNamespace(domain="existing.com")]),
            patch("app.services.competitor_discovery_service.PageRepository.list_by_website", return_value=self.pages),
            patch("app.services.competitor_discovery_service.AIModelService.resolve_execution_model", return_value=self.model),
            patch("app.services.competitor_discovery_service.AIEngineRepository.get_by_id", return_value=self.engine),
            patch("app.services.competitor_discovery_service.ProviderFactory.create", return_value=provider),
            patch("app.services.competitor_discovery_service.CompetitorDiscoveryRepository.get_by_domain", side_effect=by_domain or (lambda *_args: None)),
        ]

    def run_generate(self, response, max_candidates=5, **kwargs):
        patches = self.patches(response, **kwargs)
        for item in patches:
            item.start()
        try:
            return CompetitorDiscoveryService.generate(self.db, 8, max_candidates)
        finally:
            for item in reversed(patches):
                item.stop()

    @staticmethod
    def candidate(name, domain, *, confidence="high"):
        return {
            "brand_name": name,
            "website_url": f"https://{domain}",
            "competitor_type": "direct",
            "confidence": confidence,
            "reason": f"{name} overlaps in deployment infrastructure.",
            "evidence": [{"url": f"https://source.example/{domain}", "support": "The source describes overlapping deployment capabilities."}],
        }

    def test_filters_target_existing_and_duplicate_domains_and_respects_limit(self):
        candidates = [
            self.candidate("Vercel", "vercel.com"),
            self.candidate("Existing Cloud", "existing.com"),
            self.candidate("Alpha", "alpha.example"),
            self.candidate("Alpha Alias", "alpha.example"),
            self.candidate("Beta", "beta.example"),
            self.candidate("Gamma", "gamma.example"),
        ]

        result = self.run_generate({"candidates": candidates}, max_candidates=2)

        self.assertEqual(result["generated_count"], 2)
        self.assertEqual([item["brand_name"] for item in result["suggestions"]], ["Alpha", "Beta"])
        self.assertTrue(all(isinstance(call.args[0], CompetitorDiscoverySuggestion) for call in self.db.add.call_args_list))
        self.assertEqual(self.db.commit.call_count, 1)

    def test_ignored_suggestion_does_not_reappear_for_same_evidence(self):
        ignored = SimpleNamespace(
            status="ignored",
            evidence_fingerprint="same-fingerprint",
        )
        with patch("app.services.competitor_discovery_service.hashlib.sha256") as digest:
            digest.return_value.hexdigest.return_value = "same-fingerprint"
            result = self.run_generate(
                {"candidates": [self.candidate("Alpha", "alpha.example")]},
                existing_roles=[(self.target, "target")],
                by_domain=lambda *_args: ignored,
            )

        self.assertEqual(result["generated_count"], 0)
        self.db.add.assert_not_called()

    def test_provider_failure_creates_no_fake_suggestions(self):
        patches = self.patches({"candidates": []})
        for item in patches:
            item.start()
        try:
            with patch("app.services.competitor_discovery_service.ProviderFactory.create", side_effect=RuntimeError("provider detail")):
                with self.assertRaises(HTTPException) as raised:
                    CompetitorDiscoveryService.generate(self.db, 8, 5)
        finally:
            for item in reversed(patches):
                item.stop()

        self.assertEqual(raised.exception.status_code, 502)
        self.assertNotIn("provider detail", raised.exception.detail)
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    @patch("app.services.competitor_discovery_service.CompetitorDiscoveryRepository.list_by_project")
    @patch("app.services.competitor_discovery_service.ProjectRepository.get_by_id")
    def test_get_is_read_only(self, get_project, list_suggestions):
        get_project.return_value = self.project
        list_suggestions.return_value = []

        self.assertEqual(CompetitorDiscoveryService.list(self.db, 8), [])
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()
        self.db.flush.assert_not_called()

    @patch("app.services.competitor_discovery_service.ProjectCompetitorService.add")
    @patch("app.services.competitor_discovery_service.CompetitorDiscoveryRepository.get")
    def test_approve_uses_canonical_competitor_path_transactionally(self, get_suggestion, add_competitor):
        suggestion = SimpleNamespace(
            id=7,
            project_id=8,
            brand_name="Alpha",
            website_url="https://alpha.example",
            normalized_domain="alpha.example",
            competitor_type="direct",
            confidence="high",
            reason="Overlap.",
            evidence=[],
            status="pending",
            model_name="Test model",
            approved_brand_id=None,
        )
        get_suggestion.return_value = suggestion
        add_competitor.return_value = {"brand_id": 77, "name": "Alpha"}

        result = CompetitorDiscoveryService.approve(self.db, 8, 7)

        self.assertEqual(result["competitor"]["brand_id"], 77)
        self.assertEqual(suggestion.status, "approved")
        self.assertEqual(suggestion.approved_brand_id, 77)
        add_competitor.assert_called_once()
        self.assertFalse(add_competitor.call_args.kwargs["commit"])
        self.db.commit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
