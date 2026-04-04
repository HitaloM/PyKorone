from __future__ import annotations

from typing import Any


def coerce_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    return normalized or None


def ensure_url_scheme(url: str) -> str:
    normalized = url.strip()
    if normalized.startswith(("http://", "https://")):
        return normalized
    return f"https://{normalized.lstrip('/')}"


def coerce_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return None
    return None


def dict_or_empty(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def dict_list(value: object) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []
