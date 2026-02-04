from korone.db.repositories.disabling import DisablingRepository


async def export_disabled(chat_id: int) -> dict[str, list[str]]:
    return {"disabled": await DisablingRepository.get_disabled(chat_id)}
