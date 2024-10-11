from sophie_bot.db.models import DisablingModel


async def export_disabled(chat_id: int):
    return {"disabled": await DisablingModel.get_disabled(chat_id)}
