from ass_tg.exceptions import ArgStrictError
from ass_tg.types import OrArg, UserIDArg, UsernameArg

from sophie_bot.db.db_exceptions import DBNotFoundException
from sophie_bot.db.models import ChatModel
from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


class SophieChatIDArg(UserIDArg):
    async def value(self, text: str) -> ChatModel:
        chat_id: int = await super().value(text)

        # Find chat
        try:
            chat = await ChatModel.get_by_tid(chat_id)
            if not chat:
                raise DBNotFoundException()
            return chat
        except DBNotFoundException:
            raise ArgStrictError(_("Could not find the requested Chat ID in the database."))


class SophieChatUsernameArg(UsernameArg):
    async def value(self, text: str) -> ChatModel:
        username: str = await super().value(text)

        # Find chat
        try:
            chat = await ChatModel.find_one(ChatModel.username == username)
            if not chat:
                raise DBNotFoundException()
            return chat
        except DBNotFoundException:
            raise ArgStrictError(_("Could not find the requested Username in the database."))


class SophieChatArg(OrArg):
    def __init__(self, *args):
        description = args[0] if args else None
        super().__init__(
            SophieChatIDArg(),
            SophieChatUsernameArg(),
            description=description,
        )

    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("Chat: 'Chat ID (numeric) / Username (starts with @)'"), l_(
            "Chats: 'Chat IDs (numeric) / Usernames (starts with @)'"
        )

    @property
    def examples(self) -> dict[str, LazyProxy | None] | None:
        return {
            "-100123456789": l_("Chat ID"),
            "@SophieChat": l_("Username"),
        }
