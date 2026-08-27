import hmac
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.config import settings
from app.db.session import SessionLocal


APP_VERSION = "1.0.0"

logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.app_name,
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def require_api_token(request, call_next):
    if (
        request.url.path.startswith("/api/v1")
        and settings.api_token is not None
    ):
        expected = (
            "Bearer "
            + settings.api_token.get_secret_value()
        )
        supplied = request.headers.get(
            "authorization",
            "",
        )

        if not hmac.compare_digest(
            supplied,
            expected,
        ):
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized."},
            )

    return await call_next(request)


app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "status": "running",
        "version": APP_VERSION,
    }


@app.get("/health/live")
def liveness():
    return {
        "status": "ok",
        "version": APP_VERSION,
    }


@app.get("/health")
def readiness():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception(
            "Database readiness check failed."
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "database": "unavailable",
                "version": APP_VERSION,
            },
        )

    return {
        "status": "ok",
        "database": "available",
        "version": APP_VERSION,
    }
