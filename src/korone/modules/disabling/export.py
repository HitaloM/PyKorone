from korone.db.repositories import disabling as disabling_repo


async def export_disabled(chat_id: int) -> dict[str, list[str]]:
    return {"disabled": await disabling_repo.get_disabled(chat_id)}
