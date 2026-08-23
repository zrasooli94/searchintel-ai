from pydantic import BaseModel


class CrawlResult(BaseModel):
    website_id: int
    pages_crawled: int
    pages_discovered: int
    pages_failed: int