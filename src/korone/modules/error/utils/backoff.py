import hashlib
import time
import traceback
from typing import Final

from redis.exceptions import RedisError

from korone import aredis

# Redis-based global exponential backoff for error notifications
# Schedule: allow -> suppress 1m -> allow -> suppress 2m -> 4m -> 8m ... capped at 1h

_INITIAL_DELAY: Final[int] = 60
_FACTOR: Final[int] = 2
_MAX_DELAY: Final[int] = 3600
_QUIET_RESET: Final[int] = 1800  # reset backoff if no occurrences for 30 minutes

_PREFIX: Final[str] = "korone:err:sig:"

_SHOULD_NOTIFY_SCRIPT = aredis.register_script(
    """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local initial_delay = tonumber(ARGV[2])
local factor = tonumber(ARGV[3])
local max_delay = tonumber(ARGV[4])
local quiet_reset = tonumber(ARGV[5])

local state = redis.call("HMGET", key, "step", "next_allowed_at", "last_seen_at")
local step = tonumber(state[1] or "-1")
local next_allowed_at = tonumber(state[2] or "0")
local last_seen_at = tonumber(state[3] or "0")

if last_seen_at > 0 and now - last_seen_at > quiet_reset then
    step = -1
    next_allowed_at = 0
end

if step < 0 then
    step = 0
    local delay = math.min(initial_delay * factor ^ step, max_delay)
    local next_allowed = now + delay
    redis.call(
        "HSET",
        key,
        "step", tostring(step),
        "last_seen_at", ARGV[1],
        "last_allowed_at", ARGV[1],
        "next_allowed_at", tostring(next_allowed)
    )
    redis.call("EXPIRE", key, quiet_reset + initial_delay)
    return 1
end

if now < next_allowed_at then
    local ttl = math.floor(math.max(quiet_reset, next_allowed_at - now))
    redis.call("HSET", key, "last_seen_at", ARGV[1])
    redis.call("EXPIRE", key, ttl)
    return 0
end

step = math.min(step + 1, 32)
local delay = math.min(initial_delay * factor ^ step, max_delay)
local next_allowed = now + delay
redis.call(
    "HSET",
    key,
    "step", tostring(step),
    "last_seen_at", ARGV[1],
    "last_allowed_at", ARGV[1],
    "next_allowed_at", tostring(next_allowed)
)
redis.call("EXPIRE", key, math.floor(math.max(quiet_reset, delay)))
return 1
"""
)


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

    try:
        result = await _SHOULD_NOTIFY_SCRIPT(keys=[key], args=[now, _INITIAL_DELAY, _FACTOR, _MAX_DELAY, _QUIET_RESET])
    except RedisError:
        # Redis unavailable: be silent as requested
        return False

    return result == 1
