from __future__ import annotations

from korone.db.repositories.disabling import DisablingRepository

AI_FEATURES_KEY = "ai_features"


async def is_ai_enabled(chat_id: int) -> bool:
    disabled = await DisablingRepository.get_disabled(chat_id)
    return AI_FEATURES_KEY not in disabled


async def set_ai_enabled(chat_id: int, *, enabled: bool) -> None:
    disabled = await DisablingRepository.get_disabled(chat_id)

    if enabled:
        if AI_FEATURES_KEY not in disabled:
            return
        disabled = [cmd for cmd in disabled if cmd != AI_FEATURES_KEY]
        await DisablingRepository.set_disabled(chat_id, disabled)
        return

    if AI_FEATURES_KEY in disabled:
        return

    await DisablingRepository.set_disabled(chat_id, [*disabled, AI_FEATURES_KEY])
