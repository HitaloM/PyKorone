from __future__ import annotations

import time


def now_unix() -> int:
    return int(time.time())


def request_id(prefix: str) -> str:
    return f"{prefix}{time.time_ns()}"


def to_rounded_int(value: object, *, default: int) -> int:
    if isinstance(value, bool):
        return default

    if isinstance(value, (int, float)):
        return round(float(value))

    if isinstance(value, str):
        try:
            return round(float(value))
        except ValueError:
            return default

    return default
