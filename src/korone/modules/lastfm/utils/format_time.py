# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from datetime import UTC, datetime

from korone.modules.lastfm.utils import LastFMTrack
from korone.utils.i18n import gettext as _


def get_time_elapsed_str(track: LastFMTrack) -> str:
    played_at_datetime = datetime.fromtimestamp(track.played_at, tz=UTC)
    current_datetime = datetime.now(tz=UTC)
    time_elapsed = current_datetime - played_at_datetime

    if time_elapsed.days > 0:
        return _(", {days} day(s) ago").format(days=time_elapsed.days)

    hours, remainder = divmod(time_elapsed.seconds, 3600)
    if hours > 0:
        return _(", {hours} hour(s) ago").format(hours=hours)

    minutes, __ = divmod(remainder, 60)
    return (
        _(", {minutes} minute(s) ago").format(minutes=minutes) if minutes > 0 else _(", Just now")
    )
