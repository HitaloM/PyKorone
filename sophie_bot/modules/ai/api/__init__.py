from fastapi import APIRouter

from .moderator import router as moderator_router

api_router = APIRouter()
api_router.include_router(moderator_router)
