import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.geo_opportunity_service import (
    GeoOpportunityService,
)


class GeoOpportunityServiceTests(unittest.TestCase):

    @patch("app.services.geo_opportunity_service.GeoOpportunityRepository.list_by_experiment")
    @patch("app.services.geo_opportunity_service.ProjectBrandRepository.list_brand_roles")
    @patch("app.services.geo_opportunity_service.GeoExperimentRepository.get")
    def test_summary_reports_measured_prompts_while_analysis_is_pending(
        self,
        get_experiment,
        list_brand_roles,
        list_opportunities,
    ):
        db = Mock()
        db.scalar.return_value = 19
        get_experiment.return_value = SimpleNamespace(id=20, project_id=8)
        list_brand_roles.return_value = [(SimpleNamespace(id=50, name="Vercel"), "target")]
        list_opportunities.return_value = []

        result = GeoOpportunityService.summary(db, 20)

        self.assertEqual(result["total_prompts"], 19)
        self.assertEqual(result["analysis_status"], "pending")
        self.assertEqual(result["opportunities"], [])

    def test_no_web_search_evidence_is_unmeasured_not_target_absent(
        self,
    ):
        gap_type = GeoOpportunityService.gap_type(
            target_rate=0.0,
            competitor_pressure=0.0,
            web_search_measured=False,
        )

        self.assertEqual(
            gap_type,
            "unmeasured_web_search",
        )

    def test_measured_zero_target_rate_remains_target_absent(
        self,
    ):
        gap_type = GeoOpportunityService.gap_type(
            target_rate=0.0,
            competitor_pressure=0.0,
            web_search_measured=True,
        )

        self.assertEqual(gap_type, "target_absent")


if __name__ == "__main__":
    unittest.main()
