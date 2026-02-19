from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VulcanAPISettings:
    auth_url: str = "https://api.vulcanlabs.co/smith-auth/api/v1/token"
    chat_url: str = "https://api.vulcanlabs.co/smith-v2/api/v7/chat_android"
    application_id: str = "com.smartwidgetlabs.chatgpt"
    token_user_agent: str = "Chat Smith Android, Version 3.9.9(696)"
    chat_user_agent: str = "Chat Smith Android, Version 3.9.5(669)"
    request_id_prefix: str = "914948789"
    device_id: str = "C8DC43F3FBE1ADB9"
    x_auth_token: str = (
        "DaiExBn7Ib03PWRtbQu4HVQGUEGQKfA8GtrLN1oA8n4nOy9CdRu71OjKBwUZazZQxIgtCVQFCZtoBKgjuLVJpJTenTRjimRk"
        "aQUqZwtbXWjckIo3LeXut/Wslmkysgm9G0+lVxx38r0Eifu95+rIk5FMcZrQfZ+ubR0JkItOebU="
    )
    default_model: str = "gpt-4o-mini"
