"""Main API router aggregator."""
from fastapi import APIRouter

from app.api.scenarios import router as scenarios_router
from app.api.debates import router as debates_router
from app.api.experiments import router as experiments_router
from app.api.stream import router as stream_router
from app.api.admin import router as admin_router

api_router = APIRouter()
api_router.include_router(scenarios_router)
api_router.include_router(debates_router)
api_router.include_router(experiments_router)
api_router.include_router(stream_router)
api_router.include_router(admin_router)
