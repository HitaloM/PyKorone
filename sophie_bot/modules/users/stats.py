from stfu_tg import Code, HList, KeyValue, Section

from sophie_bot.db.models import ChatModel
from sophie_bot.db.models.chat import ChatType


async def users_stats():
    return Section(
        KeyValue(
            "Total",
            HList(
                KeyValue("users", Code(await ChatModel.total_count((ChatType.private,))), title_bold=False),
                KeyValue(
                    "groups", Code(await ChatModel.total_count((ChatType.supergroup, ChatType.group))), title_bold=False
                ),
                KeyValue("channels", Code(await ChatModel.total_count((ChatType.channel,))), title_bold=False),
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
                KeyValue("channels", Code(await ChatModel.new_count_last_48h((ChatType.channel,))), title_bold=False),
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
                KeyValue(
                    "channels", Code(await ChatModel.active_count_last_48h((ChatType.channel,))), title_bold=False
                ),
            ),
        ),
        title="Users (new)",
    )
