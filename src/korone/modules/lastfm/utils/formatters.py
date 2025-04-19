# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import re
from datetime import UTC, datetime
from html import escape
from pathlib import Path

from korone import constants
from korone.utils.i18n import gettext as _

from .lastfm_api import TimePeriod
from .types import LastFMAlbum, LastFMArtist, LastFMTrack

with Path(
    constants.BOT_ROOT_PATH / "resources/lastfm/everynoise_genres.txt",
).open(encoding="utf-8") as file:
    ACCEPTABLE_TAGS: set[str] = {line.strip().lower() for line in file}


def get_time_elapsed_str(track: LastFMTrack) -> str:
    if not track.played_at:
        return ""

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


def clean_tag_name(tag: str) -> str:
    pattern = r"[(),.;\"\'-/ ]"
    return "#" + re.sub(pattern, "_", tag.lower())


def format_tags(item: LastFMTrack | LastFMAlbum | LastFMArtist) -> str:
    if not item or not hasattr(item, "tags") or not item.tags:
        return ""

    valid_tags = [
        clean_tag_name(tag)
        for tag in (t.lower() for t in item.tags)
        if any(acceptable_tag in tag.split() for acceptable_tag in ACCEPTABLE_TAGS)
    ]

    return " ".join(valid_tags)


def period_to_str(period: TimePeriod) -> str:
    period_map = {
        TimePeriod.OneWeek: _("1 week"),
        TimePeriod.OneMonth: _("1 month"),
        TimePeriod.ThreeMonths: _("3 months"),
        TimePeriod.SixMonths: _("6 months"),
        TimePeriod.OneYear: _("1 year"),
        TimePeriod.AllTime: _("All time"),
    }

    return period_map.get(period, _("All time"))


def name_with_link(name: str, username: str) -> str:
    name = escape(name)
    return f'<a href="https://www.last.fm/user/{username}">{name}</a>'
