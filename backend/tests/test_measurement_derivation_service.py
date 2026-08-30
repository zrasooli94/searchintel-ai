import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from app.services.measurement_derivation_service import MeasurementDerivationService


class MeasurementDerivationServiceTests(unittest.TestCase):
    @patch("app.services.measurement_derivation_service.GeoOpportunityService.refresh")
    def test_web_search_refreshes_prompt_opportunities(self, refresh):
        db = Mock()
        refresh.return_value = {"total_prompts": 19}

        result = MeasurementDerivationService.refresh(db, 20, "web_search")

        refresh.assert_called_once_with(db, 20)
        self.assertEqual(result, {"total_prompts": 19})

    @patch("app.services.measurement_derivation_service.SiteRAGGapService.refresh")
    def test_site_rag_refreshes_evidence_gaps(self, refresh):
        db = Mock()
        refresh.return_value = {"total_prompts": 19, "gap_prompts": 4}

        result = MeasurementDerivationService.refresh(db, 22, "site_rag")

        refresh.assert_called_once_with(db, 22)
        self.assertEqual(result["gap_prompts"], 4)

    def test_memory_does_not_create_cross_mode_gap_analysis(self):
        self.assertIsNone(MeasurementDerivationService.refresh(Mock(), 21, "memory"))

    @patch.object(MeasurementDerivationService, "refresh")
    @patch("app.services.measurement_derivation_service.SiteRAGGapAnalysisRepository.completed_by_experiment")
    @patch("app.services.measurement_derivation_service.GeoOpportunityRepository.list_by_experiment")
    def test_backfill_refreshes_only_missing_derived_analyses(
        self,
        list_opportunities,
        completed_site_analysis,
        refresh,
    ):
        db = MagicMock()
        web_existing = SimpleNamespace(id=10, project_id=1)
        web_missing = SimpleNamespace(id=20, project_id=8)
        site_missing = SimpleNamespace(id=22, project_id=8)
        db.scalars.return_value.all.side_effect = [
            [web_existing, web_missing, site_missing],
            ["web_search"],
            ["web_search"],
            ["site_rag"],
        ]
        list_opportunities.side_effect = [[SimpleNamespace(id=1)], []]
        completed_site_analysis.return_value = None
        refresh.side_effect = [
            {"total_prompts": 19},
            {"total_prompts": 19},
        ]

        result = MeasurementDerivationService.backfill_missing(db)

        self.assertEqual(
            [item["experiment_id"] for item in result],
            [20, 22],
        )
        self.assertEqual(refresh.call_count, 2)


if __name__ == "__main__":
    unittest.main()
