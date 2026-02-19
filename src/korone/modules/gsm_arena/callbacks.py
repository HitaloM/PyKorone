from aiogram.filters.callback_data import CallbackData


class GetDeviceCallback(CallbackData, prefix="gq"):
    token: str
    index: int
    user_id: int


class DevicePageCallback(CallbackData, prefix="gp"):
    token: str
    page: int
    user_id: int
