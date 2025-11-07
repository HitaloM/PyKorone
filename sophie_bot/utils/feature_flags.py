from __future__ import annotations

import time
from typing import Final, Literal, TypedDict, Awaitable, cast

from sophie_bot.services.redis import aredis

# Public types
FeatureType = Literal[
    "ai_chatbot",
    "ai_translations",
    "ai_moderation",
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
        filters=True,
        antiflood=True,
        new_feds_newfed=False,
        new_feds_joinfed=False,
        new_feds_leavefed=False,
        new_feds_finfo=False,
        new_feds_fban=False,
        new_feds_funban=False,
        new_feds_fbanlist=False,
        new_feds_transferfed=False,
        new_feds_accepttransfer=False,
        new_feds_setlog=False,
        new_feds_unsetlog=False,
        new_feds_fsub=False,
        new_feds_funsub=False,
    )


def _from_redis_map(raw: dict[str, str]) -> FeatureStates:
    state = _default_state_map()
    for feature in FEATURE_FLAGS:
        if feature in raw:
            state[feature] = raw.get(feature) == _TRUE
    return state


async def _refresh_cache() -> None:
    global _cache, _cache_expiry
    raw = await cast(Awaitable[dict[str, str]], aredis.hgetall(_REDIS_KEY))
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
