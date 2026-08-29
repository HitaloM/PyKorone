from aiogram.enums import ChatType

from korone.db.repositories.chat import ChatRepository
from korone.ui import Code, UIExpression, field, row, section


async def users_stats() -> UIExpression:
    return section(
        "Users (new)",
        field(
            "Total",
            row(
                field("users", Code(await ChatRepository.total_count((ChatType.PRIVATE,))), bold=False),
                field(
                    "groups", Code(await ChatRepository.total_count((ChatType.SUPERGROUP, ChatType.GROUP))), bold=False
                ),
            ),
        ),
        field(
            "New (48h)",
            row(
                field("users", Code(await ChatRepository.new_count_last_48h((ChatType.PRIVATE,))), bold=False),
                field(
                    "groups",
                    Code(await ChatRepository.new_count_last_48h((ChatType.SUPERGROUP, ChatType.GROUP))),
                    bold=False,
                ),
            ),
        ),
        field(
            "Active (48h)",
            row(
                field("users", Code(await ChatRepository.active_count_last_48h((ChatType.PRIVATE,))), bold=False),
                field(
                    "groups",
                    Code(await ChatRepository.active_count_last_48h((ChatType.SUPERGROUP, ChatType.GROUP))),
                    bold=False,
                ),
            ),
        ),
    )
