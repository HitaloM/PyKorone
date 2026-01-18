from __future__ import annotations

import hashlib
import time
import traceback
from typing import Final
from redis.asyncio import Redis as AsyncRedis

from redis.exceptions import RedisError

from sophie_bot.services.redis import aredis

# Redis-based global exponential backoff for error notifications
# Schedule: allow -> suppress 1m -> allow -> suppress 2m -> 4m -> 8m ... capped at 1h

_INITIAL_DELAY: Final[int] = 60
_FACTOR: Final[int] = 2
_MAX_DELAY: Final[int] = 3600
_QUIET_RESET: Final[int] = 1800  # reset backoff if no occurrences for 30 minutes

_PREFIX: Final[str] = "sophie:err:sig:"


def compute_error_signature(exc: BaseException, frame_depth: int = 3) -> str:
    """Compute a stable signature for an exception.

    Uses exception class name, message, and top frames (from the traceback) up to frame_depth.
    Returns a hex sha256 string.
    """
    # Collect basic parts
    exc_type = type(exc).__name__
    exc_msg = str(exc)

    # Extract traceback frames; prefer exception.__traceback__
    frames: list[traceback.FrameSummary] = []
    tb = exc.__traceback__
    if tb is not None:
        frames = traceback.extract_tb(tb)
    # Use the last frames (closest to the error) and limit to frame_depth
    if frames:
        take = frames[-frame_depth:]
        frame_fps = [f"{f.filename}:{f.lineno}:{f.name}" for f in take]
    else:
        frame_fps = []

    data = "|".join([exc_type, exc_msg, *frame_fps])
    return hashlib.sha256(data.encode("utf-8", errors="ignore")).hexdigest()


async def should_notify(signature: str, now: float | None = None) -> bool:
    """Determine whether we should send a chat error notification for this error signature.

    Global across all instances via Redis. On any Redis failure, be silent (return False).
    """
    if now is None:
        now = time.time()

    key = f"{_PREFIX}{signature}"
    # Use aredis directly - it's already an AsyncRedis
    client: AsyncRedis = aredis

    try:
        # Load current state
        raw_data = await client.hgetall(key)  # type: ignore[misc]
        raw = {}
        if isinstance(raw_data, dict):
            for k, v in raw_data.items():
                rk = k.decode() if isinstance(k, bytes) else k
                rv = v.decode() if isinstance(v, bytes) else v
                raw[rk] = rv

        # Parse existing fields
        step = int(raw.get("step", "-1"))  # -1 indicates unknown/new (will be set to 0 on first allow)
        next_allowed_at = float(raw.get("next_allowed_at", "0"))
        last_seen_at = float(raw.get("last_seen_at", "0"))

        # Quiet reset: if quiet for _QUIET_RESET, reset backoff state
        if last_seen_at > 0 and now - last_seen_at > _QUIET_RESET:
            step = -1
            next_allowed_at = 0

        # Always update last_seen_at
        await client.hset(key, mapping={"last_seen_at": str(now)})  # type: ignore[misc]

        if step < 0:
            # First occurrence after reset/new: allow immediately and set initial backoff
            step = 0
            delay = min(_INITIAL_DELAY * (_FACTOR**step), _MAX_DELAY)
            next_allowed = now + delay
            await client.hset(  # type: ignore[misc]
                key,
                mapping={
                    "step": str(step),
                    "last_allowed_at": str(now),
                    "next_allowed_at": str(next_allowed),
                },
            )
            # Expire slightly past quiet reset so keys clean up
            await client.expire(key, _QUIET_RESET + _INITIAL_DELAY)
            return True

        # Existing signature
        if now < next_allowed_at:
            # Suppress within backoff window
            # Keep TTL fresh to survive through the window, but don't extend indefinitely
            await client.expire(key, int(max(_QUIET_RESET, next_allowed_at - now)))
            return False

        # Allowed now: increment step and compute next delay
        step = min(step + 1, 32)  # safety cap on exponent
        delay = min(_INITIAL_DELAY * (_FACTOR**step), _MAX_DELAY)
        next_allowed = now + delay

        await client.hset(  # type: ignore[misc]
            key,
            mapping={
                "step": str(step),
                "last_allowed_at": str(now),
                "next_allowed_at": str(next_allowed),
            },
        )
        await client.expire(key, int(max(_QUIET_RESET, delay)))
        return True

    except RedisError:
        # Redis unavailable: be silent as requested
        return False
