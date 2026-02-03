from __future__ import annotations

from enum import IntEnum

from .lastfm_api import TimePeriod


class EntryType(IntEnum):
    Artist = 1
    Album = 2
    Track = 3


def get_entry_type(split: str) -> EntryType | None:
    type_map = {"artist": EntryType.Artist, "album": EntryType.Album, "track": EntryType.Track}

    for prefix, entry_type in type_map.items():
        if split.startswith(prefix):
            return entry_type

    return None


def get_size(fragment: str) -> int | None:
    try:
        fragment_splits = fragment.split("x")
        if fragment_splits[0].isdigit():
            size = int(fragment_splits[0])
            if 0 < size <= 7:
                return size
    except ValueError, IndexError:
        pass

    return None


def get_period(split: str) -> TimePeriod | None:
    fragment = split[:4]
    first_char = split[0]

    if first_char.isdigit():
        try:
            first_digit = int(first_char)
            period_map: dict[str, tuple[int, TimePeriod] | dict[int, TimePeriod]] = {
                "d": (7, TimePeriod.OneWeek),
                "w": (1, TimePeriod.OneWeek),
                "m": {1: TimePeriod.OneMonth, 3: TimePeriod.ThreeMonths, 6: TimePeriod.SixMonths},
                "y": (1, TimePeriod.OneYear),
            }

            for key, value in period_map.items():
                if key in fragment:
                    if isinstance(value, dict):
                        return value.get(first_digit)
                    if first_digit == value[0]:
                        return value[1]
        except ValueError:
            pass
    else:
        period_key_map = {
            "w": TimePeriod.OneWeek,
            "m": TimePeriod.OneMonth,
            "y": TimePeriod.OneYear,
            "o": TimePeriod.AllTime,
            "all": TimePeriod.AllTime,
        }

        for key, period in period_key_map.items():
            if key in fragment:
                return period

    return None


def parse_collage_arg(
    arg: str | None, default_period: TimePeriod = TimePeriod.AllTime, default_entry: EntryType = EntryType.Album
) -> tuple[int, TimePeriod, EntryType, bool]:
    if not arg:
        return 3, default_period, default_entry, False

    splits = arg.lower().split()
    size = 3
    period = default_period
    no_text = any(word in splits for word in ("notext", "nonames", "clean"))
    entry_type = default_entry

    for split in splits:
        if entry_type_candidate := get_entry_type(split):
            entry_type = entry_type_candidate
            continue

        if size_candidate := get_size(split):
            size = size_candidate
            continue

        if period_candidate := get_period(split):
            period = period_candidate

    return size, period, entry_type, no_text
