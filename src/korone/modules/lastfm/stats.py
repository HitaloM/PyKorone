from stfu_tg import Code, KeyValue, Section

from korone.db.repositories.lastfm import LastFMRepository


async def lastfm_stats() -> Section:
    return Section(KeyValue("Linked users", Code(await LastFMRepository.total_count())), title="Last.fm")
