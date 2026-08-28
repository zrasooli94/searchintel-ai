import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.services.technical_seo_summary_service import (
    TechnicalSEOSummaryService,
)


class TechnicalSEOSummaryServiceTests(unittest.TestCase):

    def setUp(self):
        self.brand = SimpleNamespace(
            id=31,
            name="Example",
        )
        self.website = SimpleNamespace(
            id=44,
            domain="example.com",
            base_url="https://example.com",
            is_primary=True,
            last_crawl_summary=None,
        )
        self.patches = [
            patch(
                "app.services.technical_seo_summary_service."
                "ProjectBrandRepository.list_brand_roles",
                return_value=[(self.brand, "target")],
            ),
            patch(
                "app.services.technical_seo_summary_service."
                "WebsiteRepository.list_by_brand",
                return_value=[self.website],
            ),
            patch(
                "app.services.technical_seo_summary_service."
                "PageRepository.list_by_website",
                return_value=[],
            ),
            patch(
                "app.services.technical_seo_summary_service."
                "TechnicalAuditRepository.get_latest",
                return_value=None,
            ),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()

    def test_robots_limited_crawl_returns_limited_summary(self):
        self.website.last_crawl_summary = {
            "pages_blocked_by_robots": 1,
            "pages_discovered": 1,
            "pages_stored": 0,
        }

        result = TechnicalSEOSummaryService.build(
            db=object(),
            project_id=5,
        )

        self.assertEqual(result["project_id"], 5)
        self.assertEqual(result["measurement_state"], "limited")
        self.assertIsNone(result["audit"])
        self.assertEqual(result["crawled_pages"], 0)
        self.assertEqual(result["successful_pages"], 0)
        self.assertEqual(result["pages"], [])
        self.assertIn("SearchIntelBot", result["measurement_reason"])
        self.assertIn("does not imply", result["limitation_note"])

    def test_unattempted_project_still_returns_setup_guidance(self):
        self.website.last_crawl_summary = None

        with self.assertRaises(HTTPException) as raised:
            TechnicalSEOSummaryService.build(
                db=object(),
                project_id=9,
            )

        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(
            raised.exception.detail,
            "No technical audit exists for the target website.",
        )


if __name__ == "__main__":
    unittest.main()
