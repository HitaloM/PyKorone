from fastapi import APIRouter

from .actions import router as actions_router
from .antiflood import router as antiflood_router

api_router = APIRouter()
api_router.include_router(antiflood_router)
api_router.include_router(actions_router)

__all__ = ["api_router"]
