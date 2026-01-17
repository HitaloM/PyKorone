from typing import Any, Optional

from aiogram.types import Message
from stfu_tg.doc import Element

from sophie_bot.db.models import FiltersModel
from sophie_bot.modules.filters.types.modern_action_abc import ModernActionABC
from sophie_bot.modules.filters.types.modern_action_data_types import ACTION_DATA_DUMPED
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.modules.filters.utils_.legacy_filter_actions import (
    LEGACY_FILTERS_ACTIONS,
)
from sophie_bot.middlewares.connections import ConnectionsMiddleware
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.logger import log


async def handle_legacy_filter_action(matched_filter: FiltersModel, message: Message):
    filter_action_raw = matched_filter.action

    if not filter_action_raw:
        raise SophieException("No filter_action_raw in the filter!")

    if not (action := LEGACY_FILTERS_ACTIONS.get(filter_action_raw)):
        raise SophieException("The filter action is not supported!")

    log.debug("handle_legacy_filter", matched_filter=matched_filter)

    connected_chat = await ConnectionsMiddleware.get_current_chat_info(message.chat)
    await action["handle"](message, connected_chat, matched_filter.model_dump())


async def handle_modern_filter_action(
    message: Message, action: str, data: dict[str, Any], filter_data: ACTION_DATA_DUMPED
) -> Optional[Element | str | LazyProxy]:
    action_item: ModernActionABC = ALL_MODERN_ACTIONS[action]

    if filter_data:
        filter_data = action_item.data_object(**filter_data)

    return await action_item.handle(message, data, filter_data)
