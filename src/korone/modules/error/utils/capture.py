from typing import TYPE_CHECKING

from sentry_sdk import capture_exception

from .ignored import is_expected_exception

if TYPE_CHECKING:
    from sentry_sdk._types import Event, Hint


def before_send(event: Event, hint: Hint) -> Event | None:
    """Filter expected failures from logging, explicit and automatic captures alike."""
    exc_info = hint.get("exc_info")
    if exc_info and is_expected_exception(exc_info[1]):
        return None
    return event


def capture_sentry(exception: Exception) -> str | None:
    if is_expected_exception(exception):
        return None
    return capture_exception(exception)
