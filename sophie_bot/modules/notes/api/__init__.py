from fastapi import APIRouter

from .create import router as create_router
from .delete import router as delete_router
from .get import router as get_router
from .update import router as update_router

notes_router = APIRouter(prefix="/notes", tags=["notes"])
notes_router.include_router(get_router)
notes_router.include_router(create_router)
notes_router.include_router(update_router)
notes_router.include_router(delete_router)

__all__ = ["notes_router"]
