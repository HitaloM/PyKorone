from aiogram.types import Message

from sophie_bot.db.models import FiltersModel
from sophie_bot.modules.legacy_modules.modules.filters import LEGACY_FILTERS_ACTIONS
from sophie_bot.modules.legacy_modules.utils.connections import get_connected_chat
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.logger import log


async def handle_legacy_filter(matched_filter: FiltersModel, message: Message):
    filter_action_raw = matched_filter.action

    if not filter_action_raw:
        raise SophieException("No filter_action_raw in the filter!")

    if not (action := LEGACY_FILTERS_ACTIONS.get(filter_action_raw)):
        raise SophieException("The filter action is not supported!")

    log.debug("handle_legacy_filter", matched_filter=matched_filter)

    connected_chat = await get_connected_chat(message)
    await action["handle"](message, connected_chat, matched_filter.model_dump())
