from aiogram import Router

from .handlers.connection import router as connection_router

router = Router()
router.include_router(connection_router)
