from fastapi import APIRouter

from app.api.routes.brands import router as brands_router
from app.api.routes.projects import router as projects_router
from app.api.routes.technical_audits import router as technical_audits_router
from app.api.routes.websites import router as websites_router


api_router = APIRouter()

api_router.include_router(projects_router)
api_router.include_router(brands_router)
api_router.include_router(websites_router)
api_router.include_router(technical_audits_router)

from app.api.routes.technical_recommendations import router as technical_recommendations_router
api_router.include_router(technical_recommendations_router)
