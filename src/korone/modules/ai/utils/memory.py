from __future__ import annotations

from korone import aredis
from korone.config import CONFIG

from .keys import ai_memory_key


def _normalize_memory_line(line: str) -> str:
    return " ".join(line.split()).strip()


async def get_memory_lines(chat_id: int) -> tuple[str, ...]:
    key = ai_memory_key(chat_id)
    raw_lines = await aredis.lrange(key, 0, -1)  # type: ignore[misc]
    parsed: list[str] = []

    for raw_line in raw_lines:
        if isinstance(raw_line, bytes):
            line = raw_line.decode("utf-8", errors="ignore").strip()
        else:
            line = str(raw_line).strip()

        if line:
            parsed.append(line)

    return tuple(parsed)


async def append_memory_line(chat_id: int, information_to_save: str) -> bool:
    line = _normalize_memory_line(information_to_save)
    if not line:
        return False

    key = ai_memory_key(chat_id)
    max_lines = max(CONFIG.ai_max_memory_lines, 1)

    async with aredis.pipeline(transaction=True) as pipe:
        await pipe.lrem(key, 0, line)  # type: ignore[misc]
        await pipe.rpush(key, line)  # type: ignore[misc]
        await pipe.ltrim(key, -max_lines, -1)  # type: ignore[misc]
        await pipe.expire(key, 86400 * 30)  # type: ignore[misc]
        await pipe.execute()

    return True


async def clear_memory(chat_id: int) -> None:
    await aredis.delete(ai_memory_key(chat_id))
