import unittest
from unittest.mock import Mock, patch

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


if __name__ == "__main__":
    unittest.main()
