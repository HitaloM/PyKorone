# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import hashlib
import time
import traceback
from typing import Final

from hydrogram.errors import (
    ChannelPrivate,
    ChatWriteForbidden,
    FloodWait,
    MessageIdInvalid,
    TopicClosed,
)

IGNORED_EXCEPTIONS: tuple[type[Exception], ...] = (
    FloodWait,
    ChatWriteForbidden,
    ChannelPrivate,
    MessageIdInvalid,
    TopicClosed,
)

ERROR_NOTIFICATION_TTL: Final[float] = 300.0
_ERROR_NOTIFICATION_STATE: dict[str, float] = {}


def compute_error_signature(exc: BaseException) -> str:
    formatted_traceback = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    digest_source = f"{type(exc).__qualname__}:{formatted_traceback}"
    return hashlib.sha256(digest_source.encode("utf-8", "ignore")).hexdigest()


def should_notify(signature: str, *, ttl: float = ERROR_NOTIFICATION_TTL) -> bool:
    now = time.monotonic()

    expiry = _ERROR_NOTIFICATION_STATE.get(signature)
    if expiry and expiry > now:
        return False

    _ERROR_NOTIFICATION_STATE[signature] = now + ttl
    _purge_expired_notifications(now)
    return True


def _purge_expired_notifications(now: float) -> None:
    expired_signatures = [
        key for key, expiry in _ERROR_NOTIFICATION_STATE.items() if expiry <= now
    ]
    for signature in expired_signatures:
        _ERROR_NOTIFICATION_STATE.pop(signature, None)
