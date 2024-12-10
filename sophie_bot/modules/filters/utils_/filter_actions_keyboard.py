from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sophie_bot.modules.filters.callbacks import FilterActionCallback
from sophie_bot.modules.filters.utils_.all_modern_actions import ALL_MODERN_ACTIONS


def get_filter_actions_keyboard(exclude_filters: list[str]) -> InlineKeyboardBuilder:
    buttons = InlineKeyboardBuilder()

    for filter_action in (f for f in ALL_MODERN_ACTIONS.values() if f.name not in exclude_filters):
        buttons.row(
            InlineKeyboardButton(
                text=f"{filter_action.icon} {filter_action.title}",
                callback_data=FilterActionCallback(name=filter_action.name).pack(),
            )
        )

    return buttons
