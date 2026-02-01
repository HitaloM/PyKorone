from stfu_tg import Code, HList, KeyValue, Section

from korone.db.models.chat import ChatModel, ChatType


async def users_stats() -> Section:
    return Section(
        KeyValue(
            "Total",
            HList(
                KeyValue("users", Code(await ChatModel.total_count((ChatType.private,))), title_bold=False),
                KeyValue(
                    "groups", Code(await ChatModel.total_count((ChatType.supergroup, ChatType.group))), title_bold=False
                ),
            ),
        ),
        KeyValue(
            "New (48h)",
            HList(
                KeyValue("users", Code(await ChatModel.new_count_last_48h((ChatType.private,))), title_bold=False),
                KeyValue(
                    "groups",
                    Code(await ChatModel.new_count_last_48h((ChatType.supergroup, ChatType.group))),
                    title_bold=False,
                ),
            ),
        ),
        KeyValue(
            "Active (48h)",
            HList(
                KeyValue("users", Code(await ChatModel.active_count_last_48h((ChatType.private,))), title_bold=False),
                KeyValue(
                    "groups",
                    Code(await ChatModel.active_count_last_48h((ChatType.supergroup, ChatType.group))),
                    title_bold=False,
                ),
            ),
        ),
        title="Users (new)",
    )
