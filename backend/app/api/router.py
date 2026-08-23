from app.api.routes.prompts import router as prompts_router
from app.api.routes.ai_runs import router as ai_runs_router
from app.api.routes.ai_engines import router as ai_engines_router
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
api_router.include_router(ai_engines_router)
api_router.include_router(ai_runs_router)
api_router.include_router(prompts_router)
