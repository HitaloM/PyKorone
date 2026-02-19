from aiogram.filters.callback_data import CallbackData


class ProfileAudiosPageCallback(CallbackData, prefix="uap"):
    target_user_id: int
    requester_user_id: int
    page: int


class ProfileAudioSendCallback(CallbackData, prefix="uas"):
    target_user_id: int
    requester_user_id: int
    offset: int
