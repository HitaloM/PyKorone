from aiogram.filters.callback_data import CallbackData


class ExampleCallback(CallbackData, prefix="example"):
    action: str
    owner_id: int
