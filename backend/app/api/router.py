from app.api.routes.geo_action_plans import router as geo_action_plans_router
from app.api.routes.geo_content_diagnoses import router as geo_content_diagnoses_router
from app.api.routes.geo_opportunities import router as geo_opportunities_router
from app.api.routes.geo_experiments import router as geo_experiments_router
from app.api.routes.brand_aliases import router as brand_aliases_router
from app.api.routes.benchmarks import router as benchmarks_router
from app.api.routes.visibility_metrics import router as visibility_metrics_router
from app.api.routes.competitors import router as competitors_router
from app.api.routes.visibility import router as visibility_router
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
api_router.include_router(visibility_router)
api_router.include_router(competitors_router)
api_router.include_router(visibility_metrics_router)
api_router.include_router(benchmarks_router)
api_router.include_router(brand_aliases_router)
api_router.include_router(geo_experiments_router)
api_router.include_router(geo_opportunities_router)
api_router.include_router(geo_content_diagnoses_router)
api_router.include_router(geo_action_plans_router)
