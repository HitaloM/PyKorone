from korone.db.repositories.language import LanguageRepository


async def export_chat_language(chat_id: int) -> dict[str, str]:
    return {"language": await LanguageRepository.get_locale(chat_id)}
