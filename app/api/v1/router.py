from fastapi import APIRouter
from app.api.v1.endpoints import assessments, hazards, facilities
from app.api.v1.endpoints.config import router as config_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(assessments.router)
api_router.include_router(hazards.router)
api_router.include_router(facilities.router)
api_router.include_router(config_router, prefix="/config", tags=["config"])
