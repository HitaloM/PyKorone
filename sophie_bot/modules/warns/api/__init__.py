from fastapi import APIRouter
from .warns import router as warns_router

api_router = APIRouter()
api_router.include_router(warns_router)
