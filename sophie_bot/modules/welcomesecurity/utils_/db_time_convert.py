from datetime import timedelta

from sophie_bot.modules.legacy_modules.utils.message import convert_time


def convert_timedelta_or_str(value: str | timedelta) -> timedelta:
    if isinstance(value, timedelta):
        return value

    return convert_time(value)
