def ai_messages_key(chat_id: int) -> str:
    return f"ai:messages:{chat_id}"


def ai_memory_key(chat_id: int) -> str:
    return f"ai:memory:{chat_id}"


def ai_throttle_key(chat_id: int, user_id: int) -> str:
    return f"ai:throttle:{chat_id}:{user_id}"
