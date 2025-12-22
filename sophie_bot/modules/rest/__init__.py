from fastapi import APIRouter

from .api import router as auth_router
from .groups import router as groups_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(groups_router)

__all__ = ["api_router"]
