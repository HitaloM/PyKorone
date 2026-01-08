from aiogram.types import User
from ass_tg.entities import ArgEntities
from ass_tg.exceptions import ArgStrictError
from ass_tg.types import OrArg, UserIDArg, UserMentionArg, UsernameArg
from stfu_tg import UserLink

from sophie_bot.db.db_exceptions import DBNotFoundException
from sophie_bot.db.models import ChatModel
from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


class SophieUserIDArg(UserIDArg):
    def __init__(self, *args, allow_unknown_id: bool = False):
        super().__init__(*args)
        self.allow_unknown_id = allow_unknown_id

    async def value(self, text: str) -> ChatModel:
        user_id: int = await super().value(text)

        # Find user
        try:
            return await ChatModel.find_user(user_id)
        except DBNotFoundException:
            if not self.allow_unknown_id:
                raise ArgStrictError(_("Could not find the requested User ID in the database."))

        # Else - try to construct the user from ID
        return ChatModel.user_from_id(user_id)


class SophieUsernameArg(UsernameArg):
    async def value(self, text: str) -> ChatModel:
        username: str = await super().value(text)

        # Find user
        try:
            return await ChatModel.find_user_by_username(username)
        except DBNotFoundException:
            raise ArgStrictError(_("Could not find the requested Username in the database."))


class SophieUserMentionArg(UserMentionArg):
    async def parse(self, text: str, offset: int, entities: ArgEntities) -> tuple[int, ChatModel]:
        aiogram_user: User
        length, aiogram_user = await super().parse(text, offset, entities)

        # Find user
        try:
            user = await ChatModel.find_user(aiogram_user.id)
        except DBNotFoundException:
            # TODO: Insert user
            user = ChatModel.get_user_model(aiogram_user)

        return length, user


class SophieUserArg(OrArg):
    def __init__(self, *args, allow_unknown_id: bool = False):
        description = args[0] if args else None
        super().__init__(
            SophieUserMentionArg(),
            SophieUserIDArg(allow_unknown_id=allow_unknown_id),
            SophieUsernameArg(),
            description=description,
        )

    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("User: 'User ID (numeric) / Username (starts with @) / Mention (links to users)'"), l_(
            "Users: 'User IDs (numeric) / Usernames (starts with @) / Mentions (links to users)'"
        )

    @property
    def examples(self) -> dict[str, LazyProxy | None] | None:
        return {
            "1111224224": l_("User ID"),
            "@ofoxr_bot": l_("Username"),
            UserLink(user_id=1111224224, name="OrangeFox BOT"): l_(
                "A link to user, usually creates by mentioning a user without username."
            ),
        }  # ty:ignore[invalid-return-type]
