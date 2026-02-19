from aiogram.filters.callback_data import CallbackData


class HifiTracksPageCallback(CallbackData, prefix="hfp"):
    token: str
    page: int
    user_id: int


class HifiTrackSendCallback(CallbackData, prefix="hfs"):
    token: str
    index: int
    page: int
    user_id: int


class HifiTrackDownloadCallback(CallbackData, prefix="hfd"):
    token: str
    index: int
    user_id: int
