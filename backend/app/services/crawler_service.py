import hashlib
import re

from collections import deque
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.repositories.page_repository import PageRepository
from app.services.website_service import WebsiteService


class CrawlerService:

    USER_AGENT = "SearchIntelBot/0.1"

    @staticmethod
    def normalize_host(hostname: str | None) -> str:
        if not hostname:
            return ""

        hostname = hostname.lower()

        if hostname.startswith("www."):
            hostname = hostname[4:]

        return hostname

    @staticmethod
    def normalize_url(url: str) -> str:
        parsed = urlparse(url)

        cleaned = parsed._replace(
            fragment="",
            query="",
        )

        return urlunparse(cleaned)

    @staticmethod
    def clean_text(value: str | None) -> str | None:
        if not value:
            return None

        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def get_robots_parser(
        cls,
        client: httpx.Client,
        base_url: str,
    ) -> RobotFileParser:
        robots_url = urljoin(
            base_url,
            "/robots.txt",
        )

        parser = RobotFileParser()
        parser.set_url(robots_url)

        try:
            response = client.get(robots_url)

            if response.status_code == 200:
                parser.parse(
                    response.text.splitlines()
                )
            else:
                parser.parse([])
        except httpx.HTTPError:
            parser.parse([])

        return parser

    @classmethod
    def crawl(
        cls,
        db: Session,
        website_id: int,
        max_pages: int = 25,
    ) -> dict:
        website = WebsiteService.get(
            db,
            website_id,
        )

        start_url = cls.normalize_url(
            website.base_url
        )

        target_host = cls.normalize_host(
            urlparse(start_url).hostname
        )

        queue = deque([start_url])
        discovered = {start_url}
        visited: set[str] = set()

        pages_crawled = 0
        pages_failed = 0

        with httpx.Client(
            timeout=10.0,
            follow_redirects=True,
            headers={
                "User-Agent": cls.USER_AGENT,
            },
        ) as client:

            robots = cls.get_robots_parser(
                client,
                start_url,
            )

            while queue and pages_crawled < max_pages:
                requested_url = queue.popleft()

                if requested_url in visited:
                    continue

                visited.add(requested_url)

                if not robots.can_fetch(
                    cls.USER_AGENT,
                    requested_url,
                ):
                    continue

                try:
                    response = client.get(
                        requested_url
                    )

                    final_url = cls.normalize_url(
                        str(response.url)
                    )

                    visited.add(final_url)

                    status_code = response.status_code

                    content_type = response.headers.get(
                        "content-type",
                        "",
                    )

                    page_data = {
                        "status_code": status_code,
                        "last_crawled_at": datetime.now(
                            timezone.utc
                        ),
                    }

                    if "text/html" in content_type.lower():
                        soup = BeautifulSoup(
                            response.text,
                            "html.parser",
                        )

                        title = (
                            soup.title.get_text(
                                " ",
                                strip=True,
                            )
                            if soup.title
                            else None
                        )

                        meta_description = None

                        description_tag = soup.find(
                            "meta",
                            attrs={"name": "description"},
                        )

                        if description_tag:
                            meta_description = (
                                description_tag.get(
                                    "content"
                                )
                            )

                        h1_tags = soup.find_all("h1")
                        h1_count = len(h1_tags)

                        h1 = (
                            h1_tags[0].get_text(
                                " ",
                                strip=True,
                            )
                            if h1_tags
                            else None
                        )

                        robots_meta = None

                        robots_tag = soup.find(
                            "meta",
                            attrs={"name": "robots"},
                        )

                        if robots_tag:
                            robots_meta = robots_tag.get(
                                "content"
                            )

                        canonical_url = None

                        canonical_tag = soup.find(
                            "link",
                            rel=lambda value: (
                                value
                                and "canonical" in value
                            ),
                        )

                        if canonical_tag:
                            href = canonical_tag.get(
                                "href"
                            )

                            if href:
                                canonical_url = urljoin(
                                    final_url,
                                    href,
                                )

                        for element in soup(
                            ["script", "style", "noscript"]
                        ):
                            element.decompose()

                        content_text = cls.clean_text(
                            soup.get_text(
                                " ",
                                strip=True,
                            )
                        )

                        word_count = (
                            len(content_text.split())
                            if content_text
                            else 0
                        )

                        internal_links = set()
                        external_links = set()

                        for link in soup.find_all(
                            "a",
                            href=True,
                        ):
                            href = link.get("href")

                            if not href:
                                continue

                            absolute_url = urljoin(
                                final_url,
                                href,
                            )

                            parsed = urlparse(
                                absolute_url
                            )

                            if parsed.scheme not in {
                                "http",
                                "https",
                            }:
                                continue

                            absolute_url = cls.normalize_url(
                                absolute_url
                            )

                            link_host = cls.normalize_host(
                                parsed.hostname
                            )

                            if link_host == target_host:
                                internal_links.add(
                                    absolute_url
                                )

                                if (
                                    absolute_url
                                    not in discovered
                                ):
                                    discovered.add(
                                        absolute_url
                                    )
                                    queue.append(
                                        absolute_url
                                    )
                            else:
                                external_links.add(
                                    absolute_url
                                )

                        content_hash = (
                            hashlib.sha256(
                                content_text.encode(
                                    "utf-8"
                                )
                            ).hexdigest()
                            if content_text
                            else None
                        )

                        page_data.update(
                            {
                                "canonical_url": canonical_url,
                                "title": cls.clean_text(
                                    title
                                ),
                                "meta_description": cls.clean_text(
                                    meta_description
                                ),
                                "h1": cls.clean_text(
                                    h1
                                ),
                                "h1_count": h1_count,
                                "robots_meta": cls.clean_text(
                                    robots_meta
                                ),
                                "word_count": word_count,
                                "internal_link_count": len(
                                    internal_links
                                ),
                                "external_link_count": len(
                                    external_links
                                ),
                                "content_text": content_text,
                                "content_hash": content_hash,
                            }
                        )

                    PageRepository.upsert(
                        db=db,
                        website_id=website.id,
                        url=final_url,
                        data=page_data,
                    )

                    pages_crawled += 1

                except httpx.HTTPError:
                    pages_failed += 1

            db.commit()

        return {
            "website_id": website.id,
            "pages_crawled": pages_crawled,
            "pages_discovered": len(discovered),
            "pages_failed": pages_failed,
        }