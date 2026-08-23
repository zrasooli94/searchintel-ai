from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.repositories.page_repository import PageRepository
from app.schemas.crawl import CrawlResult
from app.schemas.page import PageRead
from app.schemas.website import WebsiteCreate, WebsiteRead
from app.services.crawler_service import CrawlerService
from app.services.website_service import WebsiteService


router = APIRouter(
    tags=["Websites"],
)


@router.post(
    "/brands/{brand_id}/websites",
    response_model=WebsiteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_website(
    brand_id: int,
    data: WebsiteCreate,
    db: Session = Depends(get_db),
):
    return WebsiteService.create(
        db,
        brand_id,
        data,
    )


@router.post(
    "/websites/{website_id}/crawl",
    response_model=CrawlResult,
)
def crawl_website(
    website_id: int,
    max_pages: int = Query(
        default=25,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    return CrawlerService.crawl(
        db=db,
        website_id=website_id,
        max_pages=max_pages,
    )


@router.get(
    "/websites/{website_id}/pages",
    response_model=list[PageRead],
)
def list_pages(
    website_id: int,
    db: Session = Depends(get_db),
):
    WebsiteService.get(
        db,
        website_id,
    )

    return PageRepository.list_by_website(
        db,
        website_id,
    )