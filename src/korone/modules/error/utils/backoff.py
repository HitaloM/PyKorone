from __future__ import annotations

import hashlib
import time
import traceback
from collections.abc import Awaitable as AwaitableABC
from typing import TYPE_CHECKING, Final, TypeVar, cast

from redis.exceptions import RedisError

from korone import aredis

if TYPE_CHECKING:
    from redis.asyncio import Redis as AsyncRedis

_INITIAL_DELAY: Final[int] = 60
_FACTOR: Final[int] = 2
_MAX_DELAY: Final[int] = 3600
_QUIET_RESET: Final[int] = 1800

_PREFIX: Final[str] = "korone:err:sig:"

T = TypeVar("T")


async def _await_if_needed(value: AwaitableABC[T] | T) -> T:
    if isinstance(value, AwaitableABC):
        return cast("T", await value)
    return value


def compute_error_signature(exc: BaseException, frame_depth: int = 3) -> str:
    exc_type = type(exc).__name__
    exc_msg = str(exc)

    frames: list[traceback.FrameSummary] = []
    tb = exc.__traceback__
    if tb is not None:
        frames = traceback.extract_tb(tb)
    if frames:
        take = frames[-frame_depth:]
        frame_fps = [f"{f.filename}:{f.lineno}:{f.name}" for f in take]
    else:
        frame_fps = []

    data = "|".join([exc_type, exc_msg, *frame_fps])
    return hashlib.sha256(data.encode("utf-8", errors="ignore")).hexdigest()


async def should_notify(signature: str, now: float | None = None) -> bool:
    if now is None:
        now = time.time()

    key = f"{_PREFIX}{signature}"
    client: AsyncRedis = aredis

    try:
        raw_data = await _await_if_needed(client.hgetall(key))
        raw: dict[str, str] = {}
        if isinstance(raw_data, dict):
            for k, v in raw_data.items():
                rk = k.decode() if isinstance(k, bytes) else str(k)
                rv = v.decode() if isinstance(v, bytes) else str(v)
                raw[rk] = rv

        step = int(raw.get("step", "-1"))
        next_allowed_at = float(raw.get("next_allowed_at", "0"))
        last_seen_at = float(raw.get("last_seen_at", "0"))

        if last_seen_at > 0 and now - last_seen_at > _QUIET_RESET:
            step = -1
            next_allowed_at = 0

        await _await_if_needed(client.hset(key, mapping={"last_seen_at": str(now)}))

        if step < 0:
            step = 0
            delay = min(_INITIAL_DELAY * (_FACTOR**step), _MAX_DELAY)
            next_allowed = now + delay
            await _await_if_needed(
                client.hset(
                    key, mapping={"step": str(step), "last_allowed_at": str(now), "next_allowed_at": str(next_allowed)}
                )
            )
            await _await_if_needed(client.expire(key, _QUIET_RESET + _INITIAL_DELAY))
            return True

        if now < next_allowed_at:
            await _await_if_needed(client.expire(key, int(max(_QUIET_RESET, next_allowed_at - now))))
            return False

        step = min(step + 1, 32)
        delay = min(_INITIAL_DELAY * (_FACTOR**step), _MAX_DELAY)
        next_allowed = now + delay

        await _await_if_needed(
            client.hset(
                key, mapping={"step": str(step), "last_allowed_at": str(now), "next_allowed_at": str(next_allowed)}
            )
        )
        await _await_if_needed(client.expire(key, int(max(_QUIET_RESET, delay))))

    except RedisError:
        return False
    else:
        return True
