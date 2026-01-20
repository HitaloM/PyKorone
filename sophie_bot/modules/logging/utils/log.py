from typing import Any, Optional, Union

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.log import LogModel
from sophie_bot.modules.logging.events import LogEvent


async def log_event(
    chat: Union[ChatModel, int],
    user: Union[ChatModel, int],
    event: LogEvent,
    details: Optional[dict[str, Any]] = None,
):
    if isinstance(chat, int):
        chat_model = await ChatModel.get_by_tid(chat)
        if not chat_model:
            return
    else:
        chat_model = chat

    if isinstance(user, int):
        user_model = await ChatModel.get_by_tid(user)
        if not user_model:
            user_model = ChatModel.user_from_id(user)
            await user_model.save()
    else:
        user_model = user

    log = LogModel(
        chat=chat_model,
        user=user_model,
        event=event.value,
        details=details or {},
    )
    await log.insert()
