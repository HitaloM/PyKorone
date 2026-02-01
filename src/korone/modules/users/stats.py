from aiogram.enums import ChatType
from stfu_tg import Code, HList, KeyValue, Section

from korone.db.repositories import chat as chat_repo


async def users_stats() -> Section:
    return Section(
        KeyValue(
            "Total",
            HList(
                KeyValue("users", Code(await chat_repo.total_count((ChatType.PRIVATE,))), title_bold=False),
                KeyValue(
                    "groups", Code(await chat_repo.total_count((ChatType.SUPERGROUP, ChatType.GROUP))), title_bold=False
                ),
            ),
        ),
        KeyValue(
            "New (48h)",
            HList(
                KeyValue("users", Code(await chat_repo.new_count_last_48h((ChatType.PRIVATE,))), title_bold=False),
                KeyValue(
                    "groups",
                    Code(await chat_repo.new_count_last_48h((ChatType.SUPERGROUP, ChatType.GROUP))),
                    title_bold=False,
                ),
            ),
        ),
        KeyValue(
            "Active (48h)",
            HList(
                KeyValue("users", Code(await chat_repo.active_count_last_48h((ChatType.PRIVATE,))), title_bold=False),
                KeyValue(
                    "groups",
                    Code(await chat_repo.active_count_last_48h((ChatType.SUPERGROUP, ChatType.GROUP))),
                    title_bold=False,
                ),
            ),
        ),
        title="Users (new)",
    )
