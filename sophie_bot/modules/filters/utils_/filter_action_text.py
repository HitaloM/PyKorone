from typing import Optional

from stfu_tg import Section, VList
from stfu_tg.doc import Element as StfuElement

from sophie_bot.modules.filters.types.modern_action_abc import ModernActionABC
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS
from sophie_bot.modules.filters.utils_.legacy_filter_actions import (
    LEGACY_FILTERS_ACTIONS,
)
from sophie_bot.utils.i18n import LazyProxy


def get_modern_action_text(action: ModernActionABC):
    return f"{action.icon} {action.title}"


def filter_action_text(action: Optional[str], actions: Optional[list[str]]) -> StfuElement | LazyProxy:
    if not actions and not action:
        raise TypeError("No action provided for filter_action_text")

    if not actions:
        # Legacy filter
        legacy_item = LEGACY_FILTERS_ACTIONS[action]  # type: ignore
        return legacy_item["title"]

    if len(actions) == 1:
        return get_modern_action_text(ALL_MODERN_ACTIONS[actions[0]])

    return Section(VList(*(get_modern_action_text(ALL_MODERN_ACTIONS[action]) for action in actions), indent=2))
