import unittest

from pydantic import ValidationError

from app.schemas.project_competitor import (
    ProjectCompetitorCreate,
)
from app.schemas.project_onboarding import (
    ProjectOnboardRequest,
)


class BrandValidationTests(unittest.TestCase):

    def test_single_character_target_brand_is_valid(self):
        request = ProjectOnboardRequest(
            project_name="X Validation",
            target_brand="X",
            website_url="https://x.com/",
        )

        self.assertEqual(request.target_brand, "X")

    def test_single_character_competitor_is_valid(self):
        request = ProjectCompetitorCreate(
            name="X",
            website_url="https://x.com/",
        )

        self.assertEqual(request.name, "X")

    def test_empty_competitor_is_rejected(self):
        with self.assertRaises(ValidationError):
            ProjectCompetitorCreate(name="")


if __name__ == "__main__":
    unittest.main()
