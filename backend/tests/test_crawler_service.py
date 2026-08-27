import unittest

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.crawler_service import CrawlerService


class _Response:

    def __init__(
        self,
        *,
        url: str,
        text: str,
        status_code: int = 200,
        content_type: str = "text/plain",
    ):
        self.url = url
        self.text = text
        self.status_code = status_code
        self.headers = {
            "content-type": content_type,
        }


class _RobotsBlockedClient:

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url: str):
        if url.endswith("/robots.txt"):
            return _Response(
                url=url,
                text=(
                    "User-agent: SearchIntelBot\n"
                    "Disallow: /\n"
                ),
            )

        raise AssertionError(
            "A robots-blocked page must not be fetched."
        )


class CrawlerServiceTests(unittest.TestCase):

    @patch(
        "app.services.crawler_service.httpx.Client",
        _RobotsBlockedClient,
    )
    @patch(
        "app.services.crawler_service.PageRepository.upsert",
    )
    @patch(
        "app.services.crawler_service.WebsiteService.get",
    )
    def test_robots_block_is_reported_as_a_crawl_limitation(
        self,
        get_website,
        upsert_page,
    ):
        get_website.return_value = SimpleNamespace(
            id=17,
            base_url="https://example.com/",
        )
        db = Mock()

        result = CrawlerService.crawl(
            db,
            website_id=17,
            max_pages=5,
        )

        self.assertEqual(result["pages_crawled"], 0)
        self.assertEqual(
            result["pages_blocked_by_robots"],
            1,
        )
        self.assertTrue(result["crawl_limited"])
        self.assertIn(
            "robots policy blocked 1 discovered URL",
            result["limitations"][0],
        )
        upsert_page.assert_not_called()
        db.commit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
