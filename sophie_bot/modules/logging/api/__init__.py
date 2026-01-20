from fastapi import APIRouter
from .logs import router as logs_router

api_router = APIRouter()
api_router.include_router(logs_router)
