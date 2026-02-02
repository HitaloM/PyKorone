from __future__ import annotations

from korone.modules.gsm_arena.utils.scraper import check_phone_details, format_phone


async def get_device_text(url: str) -> str | None:
    if phone := await check_phone_details(url):
        return format_phone(phone)
    return None
