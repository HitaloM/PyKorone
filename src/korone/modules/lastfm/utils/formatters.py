# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from datetime import UTC, datetime
from html import escape
from pathlib import Path

from korone import app_dir
from korone.modules.lastfm.utils.api import TimePeriod
from korone.modules.lastfm.utils.types import LastFMAlbum, LastFMArtist, LastFMTrack
from korone.utils.i18n import gettext as _

with Path(app_dir / "resources/misc/everynoise_genres.txt").open(encoding="utf-8") as file:
    ACCEPTABLE_TAGS = {line.strip().lower() for line in file}


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


def format_tags(item: LastFMTrack | LastFMAlbum | LastFMArtist) -> str:
    tags_text = ""
    if item:
        tags_text = " ".join(
            f"#{
                t.replace("(", "_")
                .replace(")", "_")
                .replace(",", "_")
                .replace('"', "_")
                .replace(".", "_")
                .replace(";", "_")
                .replace(":", "_")
                .replace("'", "_")
                .replace("-", "_")
                .replace(" ", "_")
                .replace("/", "_")
            }"
            for t in (tag.lower() for tag in item.tags or [])
            if any(x in ACCEPTABLE_TAGS for x in t.split(" "))
        )
    return tags_text


def period_to_str(period: TimePeriod) -> str:
    if period == TimePeriod.OneWeek:
        return _("1 week")
    if period == TimePeriod.OneMonth:
        return _("1 month")
    if period == TimePeriod.ThreeMonths:
        return _("3 months")
    if period == TimePeriod.SixMonths:
        return _("6 months")
    if period == TimePeriod.OneYear:
        return _("1 year")
    return _("All time")


def name_with_link(name: str, username: str) -> str:
    name = escape(name)
    return f'<a href="https://www.last.fm/user/{username}">{name}</a>'
