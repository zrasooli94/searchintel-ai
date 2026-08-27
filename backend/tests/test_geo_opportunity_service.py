import unittest

from app.services.geo_opportunity_service import (
    GeoOpportunityService,
)


class GeoOpportunityServiceTests(unittest.TestCase):

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
