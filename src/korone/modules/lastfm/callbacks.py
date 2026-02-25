from enum import StrEnum

from aiogram.filters.callback_data import CallbackData

from .utils.periods import LastFMPeriod  # noqa: TC001


class LastFMMode(StrEnum):
    COMPACT = "c"
    EXPANDED = "e"


class LastFMViewCallback(CallbackData, prefix="lfmv"):
    u: str
    m: LastFMMode
    uid: int


class LastFMRefreshCallback(CallbackData, prefix="lfmr"):
    u: str
    m: LastFMMode
    uid: int


class LastFMInfoCallback(CallbackData, prefix="lfmi"):
    u: str
    uid: int


class LastFMAlbumRefreshCallback(CallbackData, prefix="lfmar"):
    u: str
    uid: int


class LastFMAlbumInfoCallback(CallbackData, prefix="lfmai"):
    u: str
    uid: int


class LastFMArtistRefreshCallback(CallbackData, prefix="lfmtr"):
    u: str
    uid: int


class LastFMArtistInfoCallback(CallbackData, prefix="lfmti"):
    u: str
    uid: int


class LastFMCollageCallback(CallbackData, prefix="lfmco"):
    uid: int
    tid: int
    s: int
    p: LastFMPeriod
    t: int
