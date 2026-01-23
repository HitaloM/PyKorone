from korone.db.models.language import LanguageModel


async def export_chat_language(chat_id: int):
    return {"language": await LanguageModel.get_locale(chat_id)}
