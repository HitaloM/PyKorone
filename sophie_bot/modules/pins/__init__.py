from aiogram import Router

from .handlers.pin import PinHandler
from .handlers.unpin import UnpinHandler

router = Router(name="pins")
__handlers__ = [PinHandler, UnpinHandler]
