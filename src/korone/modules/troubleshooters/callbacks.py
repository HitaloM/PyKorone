from aiogram.filters.callback_data import CallbackData


class CancelCallback(CallbackData, prefix="cancel"):
    user_id: int


class CallbackActionCancel(CallbackData, prefix="cancel_action"):
    pass
