from fastapi import APIRouter
from .get_settings import router as get_settings_router
from .update_settings import router as update_settings_router
from .get_user_warns import router as get_user_warns_router
from .delete_warn import router as delete_warn_router

api_router = APIRouter()
api_router.include_router(get_settings_router)
api_router.include_router(update_settings_router)
api_router.include_router(get_user_warns_router)
api_router.include_router(delete_warn_router)
