from datetime import timedelta
import re


def convert_timedelta_or_str(value: str | timedelta) -> timedelta:
    if isinstance(value, timedelta):
        return value

    # Simple implementation to handle basics if original is lost
    # Format usually like "1d", "1h", "10m"
    if not isinstance(value, str):
        raise ValueError(f"Cannot convert {type(value)} to timedelta")

    value = value.lower()
    if value.endswith("d"):
        return timedelta(days=int(value[:-1]))
    elif value.endswith("h"):
        return timedelta(hours=int(value[:-1]))
    elif value.endswith("m"):
        return timedelta(minutes=int(value[:-1]))
    elif value.endswith("s"):
        return timedelta(seconds=int(value[:-1]))
    elif value.endswith("w"):
        return timedelta(weeks=int(value[:-1]))

    return timedelta(seconds=0)
