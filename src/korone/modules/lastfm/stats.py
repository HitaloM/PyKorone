from korone.db.repositories.lastfm import LastFMRepository
from korone.utils.formatting import Code, KeyValue, Section


async def lastfm_stats() -> Section:
    linked_users_total = await LastFMRepository.total_count()
    return Section(KeyValue("Linked users", Code(linked_users_total)), title="Last.fm")
