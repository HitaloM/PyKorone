from __future__ import annotations

from enum import StrEnum

from korone.utils.i18n import gettext as _


class LastFMPeriod(StrEnum):
    OVERALL = "overall"
    ONE_WEEK = "7day"
    ONE_MONTH = "1month"
    THREE_MONTHS = "3month"
    SIX_MONTHS = "6month"
    ONE_YEAR = "12month"


_PERIOD_ALIASES: dict[str, LastFMPeriod] = {
    "all": LastFMPeriod.OVERALL,
    "overall": LastFMPeriod.OVERALL,
    "alltime": LastFMPeriod.OVERALL,
    "all-time": LastFMPeriod.OVERALL,
    "7d": LastFMPeriod.ONE_WEEK,
    "7day": LastFMPeriod.ONE_WEEK,
    "1w": LastFMPeriod.ONE_WEEK,
    "week": LastFMPeriod.ONE_WEEK,
    "1week": LastFMPeriod.ONE_WEEK,
    "1m": LastFMPeriod.ONE_MONTH,
    "month": LastFMPeriod.ONE_MONTH,
    "1month": LastFMPeriod.ONE_MONTH,
    "3m": LastFMPeriod.THREE_MONTHS,
    "3month": LastFMPeriod.THREE_MONTHS,
    "3months": LastFMPeriod.THREE_MONTHS,
    "6m": LastFMPeriod.SIX_MONTHS,
    "6month": LastFMPeriod.SIX_MONTHS,
    "6months": LastFMPeriod.SIX_MONTHS,
    "1y": LastFMPeriod.ONE_YEAR,
    "1year": LastFMPeriod.ONE_YEAR,
    "12m": LastFMPeriod.ONE_YEAR,
    "12month": LastFMPeriod.ONE_YEAR,
    "year": LastFMPeriod.ONE_YEAR,
}


def parse_period_token(raw_value: str, *, default: LastFMPeriod) -> LastFMPeriod:
    normalized = raw_value.strip().lower()
    return _PERIOD_ALIASES.get(normalized, default)


def period_label(period: LastFMPeriod) -> str:
    match period:
        case LastFMPeriod.ONE_WEEK:
            return _("1 week")
        case LastFMPeriod.ONE_MONTH:
            return _("1 month")
        case LastFMPeriod.THREE_MONTHS:
            return _("3 months")
        case LastFMPeriod.SIX_MONTHS:
            return _("6 months")
        case LastFMPeriod.ONE_YEAR:
            return _("1 year")
        case _:
            return _("all-time")
