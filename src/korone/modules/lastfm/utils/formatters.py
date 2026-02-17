from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from stfu_tg import Template, Url

from korone.utils.i18n import gettext as _

from .lastfm_api import TimePeriod

if TYPE_CHECKING:
    from .types import LastFMAlbum, LastFMArtist, LastFMTrack


TAG_CLEAN_RE = re.compile(r"[(),.;\"\'\-/ ]")
PERIOD_LABELS = {
    TimePeriod.OneWeek: _("1 week"),
    TimePeriod.OneMonth: _("1 month"),
    TimePeriod.ThreeMonths: _("3 months"),
    TimePeriod.SixMonths: _("6 months"),
    TimePeriod.OneYear: _("1 year"),
    TimePeriod.AllTime: _("All time"),
}


def get_time_elapsed_str(track: LastFMTrack) -> str:
    if not track.played_at:
        return ""

    played_at_datetime = datetime.fromtimestamp(track.played_at, tz=UTC)
    current_datetime = datetime.now(tz=UTC)
    time_elapsed = current_datetime - played_at_datetime

    if time_elapsed.days > 0:
        return Template(_(", {days} day(s) ago"), days=time_elapsed.days).to_html()

    hours, remainder = divmod(time_elapsed.seconds, 3600)
    if hours > 0:
        return Template(_(", {hours} hour(s) ago"), hours=hours).to_html()

    minutes, __ = divmod(remainder, 60)
    return Template(_(", {minutes} minute(s) ago"), minutes=minutes).to_html() if minutes > 0 else _(", Just now")


def clean_tag_name(tag: str) -> str:
    return "#" + TAG_CLEAN_RE.sub("_", tag.lower())


def format_tags(item: LastFMTrack | LastFMAlbum | LastFMArtist) -> str:
    if not item or not hasattr(item, "tags") or not item.tags:
        return ""

    raw_tags = item.tags if isinstance(item.tags, list) else [item.tags]
    seen: set[str] = set()
    cleaned_tags: list[str] = []
    for tag in raw_tags:
        if not tag:
            continue
        cleaned = clean_tag_name(tag)
        if cleaned in seen:
            continue
        seen.add(cleaned)
        cleaned_tags.append(cleaned)

    return " ".join(cleaned_tags)


def period_to_str(period: TimePeriod) -> str:
    return PERIOD_LABELS.get(period, PERIOD_LABELS[TimePeriod.AllTime])


def name_with_link(name: str, username: str) -> str:
    return Url(name, f"https://www.last.fm/user/{username}").to_html()
