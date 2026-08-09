from fastapi import APIRouter

from app.api.routes.agent import router as agent_router
from app.api.routes.clubs import router as clubs_router
from app.api.routes.form import router as form_router
from app.api.routes.health import router as health_router
from app.api.routes.matches import router as matches_router
from app.api.routes.players import router as players_router
from app.api.routes.standings import router as standings_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(clubs_router)
api_router.include_router(standings_router)
api_router.include_router(form_router)
api_router.include_router(players_router)
api_router.include_router(matches_router)
api_router.include_router(agent_router)
