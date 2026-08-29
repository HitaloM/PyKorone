from korone.db.repositories.lastfm import LastFMRepository
from korone.ui import Code, UIExpression, field, section


async def lastfm_stats() -> UIExpression:
    linked_users_total = await LastFMRepository.total_count()
    return section("Last.fm", field("Linked users", Code(linked_users_total)))
