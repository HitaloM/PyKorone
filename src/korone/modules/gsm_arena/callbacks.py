from aiogram.filters.callback_data import CallbackData


class GetDeviceCallback(CallbackData, prefix="gsm_query"):
    device: str


class DevicePageCallback(CallbackData, prefix="gsm_qpage"):
    device: str
    page: int
