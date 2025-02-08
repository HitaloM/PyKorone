from aiogram.enums import ChatType
from beanie.odm.operators.find.comparison import In

from sophie_bot.db.models import ChatModel


class ForChats:
    """A sugar syntax for iterating over chats for schedulers"""

    def __init__(self, chat_types: tuple[ChatType, ...] = (ChatType.GROUP, ChatType.SUPERGROUP)):
        self.chat_types = chat_types

    def __aiter__(self):
        return ChatModel.find(In(ChatModel.type, self.chat_types)).__aiter__()
