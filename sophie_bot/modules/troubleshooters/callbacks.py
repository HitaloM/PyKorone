from aiogram.filters.callback_data import CallbackData


class CancelCallback(CallbackData, prefix="cancel"):
    user_id: int  # User ID that can cancel the action
