from stfu_tg import Code, KeyValue, Section

from korone.db.repositories.lastfm import LastFMRepository


async def lastfm_stats() -> Section:
    linked_users_total = await LastFMRepository.total_count()
    return Section(KeyValue("Linked users", Code(linked_users_total)), title="Last.fm")
