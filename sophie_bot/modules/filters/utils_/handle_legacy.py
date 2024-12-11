from aiogram.types import Message

from sophie_bot.db.models import FiltersModel
from sophie_bot.modules.legacy_modules.modules.filters import LEGACY_FILTERS_ACTIONS
from sophie_bot.modules.legacy_modules.utils.connections import get_connected_chat
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.logger import log


async def handle_legacy_filter(matched_filter: FiltersModel, message: Message):
    if not (action := LEGACY_FILTERS_ACTIONS.get(matched_filter.action)):
        raise SophieException("The filter action is not supported!")

    log.debug("handle_legacy_filter", matched_filter=matched_filter)

    connected_chat = await get_connected_chat(message)
    await action["handle"](message, connected_chat, matched_filter.model_dump())
