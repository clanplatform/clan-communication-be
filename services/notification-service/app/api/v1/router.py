from fastapi import APIRouter

from app.api.v1.endpoints import notifications, templates, preferences

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(notifications.router)
api_router.include_router(templates.router)
api_router.include_router(preferences.router)
