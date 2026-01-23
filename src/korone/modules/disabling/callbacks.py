from aiogram.filters.callback_data import CallbackData


class EnableAllCallback(CallbackData, prefix="enable_all"):
    user_id: int
