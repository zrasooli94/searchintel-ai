from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
    }