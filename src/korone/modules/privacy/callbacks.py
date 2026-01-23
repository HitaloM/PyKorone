from aiogram.filters.callback_data import CallbackData


class PrivacyMenuCallback(CallbackData, prefix="privacy"):
    back_to_start: bool = False
