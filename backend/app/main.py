from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
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