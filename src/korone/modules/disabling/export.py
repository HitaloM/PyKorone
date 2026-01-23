from korone.db.models.disabling import DisablingModel


async def export_disabled(chat_id: int):
    return {"disabled": await DisablingModel.get_disabled(chat_id)}
