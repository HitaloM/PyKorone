from korone.db.repositories import language as language_repo


async def export_chat_language(chat_id: int) -> dict[str, str]:
    return {"language": await language_repo.get_locale(chat_id)}
