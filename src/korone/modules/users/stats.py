from aiogram.enums import ChatType
from stfu_tg import Code, HList, KeyValue, Section

from korone.db.repositories.chat import ChatRepository


async def users_stats() -> Section:
    return Section(
        KeyValue(
            "Total",
            HList(
                KeyValue("users", Code(await ChatRepository.total_count((ChatType.PRIVATE,))), title_bold=False),
                KeyValue(
                    "groups",
                    Code(await ChatRepository.total_count((ChatType.SUPERGROUP, ChatType.GROUP))),
                    title_bold=False,
                ),
            ),
        ),
        KeyValue(
            "New (48h)",
            HList(
                KeyValue("users", Code(await ChatRepository.new_count_last_48h((ChatType.PRIVATE,))), title_bold=False),
                KeyValue(
                    "groups",
                    Code(await ChatRepository.new_count_last_48h((ChatType.SUPERGROUP, ChatType.GROUP))),
                    title_bold=False,
                ),
            ),
        ),
        KeyValue(
            "Active (48h)",
            HList(
                KeyValue(
                    "users", Code(await ChatRepository.active_count_last_48h((ChatType.PRIVATE,))), title_bold=False
                ),
                KeyValue(
                    "groups",
                    Code(await ChatRepository.active_count_last_48h((ChatType.SUPERGROUP, ChatType.GROUP))),
                    title_bold=False,
                ),
            ),
        ),
        title="Users (new)",
    )
