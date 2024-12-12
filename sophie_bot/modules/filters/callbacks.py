from aiogram.filters.callback_data import CallbackData


class FilterActionCallback(CallbackData, prefix="filter_action_modern"):
    # Action name
    name: str
