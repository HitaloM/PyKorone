from typing import Any, Awaitable, Callable, TypedDict

from aiogram.types import Chat, Message

from sophie_bot.utils.i18n import LazyProxy


class LegacyFilterAction(TypedDict):
    title: LazyProxy
    handle: Callable[[Message, Chat, dict], Awaitable[Any]]
    action: Callable[[Message, dict], str]
    del_btn_name: Callable[[Message, dict], str] | None
    setup: list[dict] | dict | None


LEGACY_FILTERS_ACTIONS: dict[str, LegacyFilterAction] = {}
