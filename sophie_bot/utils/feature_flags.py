from __future__ import annotations

import time
from typing import Final, Literal, TypedDict, Awaitable, cast, Any

from sophie_bot.services.redis import aredis

# Public types
FeatureType = Literal[
    "ai_chatbot",
    "ai_translations",
    "ai_moderation",
    "ai_filters",
    "filters",
    "antiflood",
    "new_feds_newfed",
    "new_feds_joinfed",
    "new_feds_leavefed",
    "new_feds_finfo",
    "new_feds_fban",
    "new_feds_funban",
    "new_feds_fbanlist",
    "new_feds_transferfed",
    "new_feds_accepttransfer",
    "new_feds_setlog",
    "new_feds_unsetlog",
    "new_feds_fsub",
    "new_feds_funsub",
]

# Redis storage details
_REDIS_KEY: Final[str] = "sophie:kill_switch"
_TRUE: Final[str] = "1"
_FALSE: Final[str] = "0"

# In-process cache
_TTL_SECONDS: Final[float] = 2.0
_cache: dict[str, bool] = {}
_cache_expiry: float = 0.0


class FeatureStates(TypedDict):
    ai_chatbot: bool
    ai_translations: bool
    ai_moderation: bool
    ai_filters: bool
    filters: bool
    antiflood: bool
    new_feds_newfed: bool
    new_feds_joinfed: bool
    new_feds_leavefed: bool
    new_feds_finfo: bool
    new_feds_fban: bool
    new_feds_funban: bool
    new_feds_fbanlist: bool
    new_feds_transferfed: bool
    new_feds_accepttransfer: bool
    new_feds_setlog: bool
    new_feds_unsetlog: bool
    new_feds_fsub: bool
    new_feds_funsub: bool


FEATURE_FLAGS: Final[tuple[FeatureType, ...]] = (
    "ai_chatbot",
    "ai_translations",
    "ai_moderation",
    "ai_filters",
    "filters",
    "antiflood",
    "new_feds_newfed",
    "new_feds_joinfed",
    "new_feds_leavefed",
    "new_feds_finfo",
    "new_feds_fban",
    "new_feds_funban",
    "new_feds_fbanlist",
    "new_feds_transferfed",
    "new_feds_accepttransfer",
    "new_feds_setlog",
    "new_feds_unsetlog",
    "new_feds_fsub",
    "new_feds_funsub",
)


def _now() -> float:
    return time.monotonic()


def _default_state_map() -> FeatureStates:
    # Missing values are treated as enabled (True) by default for kill switches
    # Federation features default to False (disabled) to enable slowly
    return FeatureStates(
        ai_chatbot=True,
        ai_translations=True,
        ai_moderation=True,
        ai_filters=True,
        filters=True,
        antiflood=True,
        new_feds_newfed=True,
        new_feds_joinfed=True,
        new_feds_leavefed=True,
        new_feds_finfo=True,
        new_feds_fban=True,
        new_feds_funban=True,
        new_feds_fbanlist=True,
        new_feds_transferfed=True,
        new_feds_accepttransfer=True,
        new_feds_setlog=True,
        new_feds_unsetlog=True,
        new_feds_fsub=True,
        new_feds_funsub=True,
    )


def _from_redis_map(raw: dict[str, str]) -> FeatureStates:
    state = _default_state_map()
    for feature in FEATURE_FLAGS:
        if feature in raw:
            state[feature] = raw.get(feature) == _TRUE
    return state


async def _refresh_cache() -> None:
    global _cache, _cache_expiry
    raw_data = await cast(Awaitable[Any], aredis.hgetall(_REDIS_KEY))
    raw = {}
    if isinstance(raw_data, dict):
        for k, v in raw_data.items():
            key = k.decode() if isinstance(k, bytes) else k
            val = v.decode() if isinstance(v, bytes) else v
            raw[key] = val

    states = _from_redis_map(raw)
    # Build cache explicitly to preserve precise typing (bool values)
    _cache = {feature: states[feature] for feature in FEATURE_FLAGS}
    _cache_expiry = _now() + _TTL_SECONDS


async def is_enabled(feature: FeatureType) -> bool:
    global _cache, _cache_expiry
    if _now() >= _cache_expiry:
        await _refresh_cache()
    # Default to True if somehow missing
    return _cache.get(feature, True)


async def set_enabled(feature: FeatureType, enabled: bool) -> None:
    global _cache, _cache_expiry
    _ = await cast(Awaitable[int], aredis.hset(_REDIS_KEY, feature, _TRUE if enabled else _FALSE))
    # Update local cache immediately
    if _now() >= _cache_expiry:
        # If cache expired, refresh fully to include any other changes
        await _refresh_cache()
    else:
        _cache[feature] = enabled


async def list_all() -> FeatureStates:
    global _cache, _cache_expiry
    if _now() >= _cache_expiry:
        await _refresh_cache()
    # Ensure all features present with defaults
    merged = _default_state_map()
    for feature in FEATURE_FLAGS:
        if feature in _cache:
            merged[feature] = _cache[feature]
    return merged
