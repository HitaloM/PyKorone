from __future__ import annotations

from typing import TYPE_CHECKING

from korone.modules.hifi.callbacks import HifiTrackSendCallback, HifiTracksPageCallback
from korone.modules.utils_.pagination import Pagination

from .formatters import RESULTS_PER_PAGE, format_track_button

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup

    from .types import HifiSearchSession


def create_tracks_keyboard(session: HifiSearchSession, token: str, page: int, user_id: int) -> InlineKeyboardMarkup:
    indexed_tracks = list(enumerate(session.tracks))

    pagination = Pagination(
        objects=indexed_tracks,
        page_data=lambda page_number: HifiTracksPageCallback(token=token, page=page_number, user_id=user_id).pack(),
        item_data=lambda item, page_number: HifiTrackSendCallback(
            token=token, index=item[0], page=page_number, user_id=user_id
        ).pack(),
        item_title=lambda item, _: format_track_button(item[0], item[1]),
    )

    return pagination.create(page=page, lines=RESULTS_PER_PAGE, columns=1)
