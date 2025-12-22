from typing import Any

from sophie_bot.db.models import ChatModel
from sophie_bot.utils.exception import SophieException


async def privacy_export(chat_id: int) -> dict[str, Any]:
    chat = await ChatModel.get_by_tid(chat_id)

    if not chat:
        raise SophieException("Chat not found in the database.")

    # if chat.type == ChatType.private:
    #     groups_of_user = chat.groups_of_user

    return {"chat_db": ChatModel.export_dict(chat)}
