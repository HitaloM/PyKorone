from korone.db.repositories.lastfm import LastFMRepository


async def export_lastfm(chat_id: int) -> dict[str, dict[str, str | None]]:
    username = await LastFMRepository.get_username(chat_id)
    return {"lastfm": {"username": username}}
