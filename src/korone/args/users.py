from ass_tg.entities import ArgEntities
from ass_tg.exceptions import ArgStrictError
from ass_tg.types import OrArg
from ass_tg.types.base_abc import ArgFabric
from stfu_tg import UserLink

from korone.db.db_exceptions import DBNotFoundException
from korone.db.models.chat import ChatModel
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_


class KoroneUserIDArg(ArgFabric):
    __slots__ = ("allow_unknown_id",)

    def __init__(self, *args, allow_unknown_id: bool = False):
        super().__init__(*args)
        self.allow_unknown_id = allow_unknown_id

    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("User ID (Numeric)"), l_("User IDs (Numeric)")

    def check(self, text: str, entities: ArgEntities) -> bool:
        return text.split()[0].lstrip("-").isdigit()

    async def parse(self, text: str, offset: int, entities: ArgEntities) -> tuple[int, ChatModel]:
        user_id = int(text.split()[0])
        length = len(str(user_id))

        try:
            user = await ChatModel.find_user(user_id)
            return length, user
        except DBNotFoundException:
            if not self.allow_unknown_id:
                raise ArgStrictError(_("Could not find the requested User ID in the database."))

        return length, ChatModel.user_from_id(user_id)


class KoroneUsernameArg(ArgFabric):
    prefix: str = "@"

    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("Username (starts with @)"), l_("Usernames (starts with @)")

    def check(self, text: str, entities: ArgEntities) -> bool:
        return text.split()[0].startswith(self.prefix)

    async def parse(self, text: str, offset: int, entities: ArgEntities) -> tuple[int, ChatModel]:
        username = text.split()[0].removeprefix(self.prefix)
        length = len(username) + len(self.prefix)

        try:
            user = await ChatModel.find_user_by_username(username)
            return length, user
        except DBNotFoundException:
            raise ArgStrictError(_("Could not find the requested Username in the database."))


class KoroneUserMentionArg(ArgFabric):
    _allowed_entities = ("mention", "text_mention")

    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("User mention"), l_("User mentions")

    def check(self, text: str, entities: ArgEntities) -> bool:
        return any(e.offset == 0 and e.type in self._allowed_entities for e in entities)

    async def parse(self, text: str, offset: int, entities: ArgEntities) -> tuple[int, ChatModel]:
        mention_entities = [e for e in entities if e.offset == offset and e.type in self._allowed_entities]
        if not mention_entities:
            raise ArgStrictError(_("No mention entity found at offset."))

        entity = mention_entities[0]
        mention_text = text[entity.offset : entity.offset + entity.length]
        length = entity.length

        if entity.type == "text_mention" and entity.user:
            aiogram_user = entity.user
        else:
            username = mention_text.lstrip("@")
            try:
                user = await ChatModel.find_user_by_username(username)
                return length, user
            except DBNotFoundException:
                raise ArgStrictError(_("Could not find the mentioned user in the database."))

        try:
            user = await ChatModel.find_user(aiogram_user.id)
        except DBNotFoundException:
            user = await ChatModel.upsert_user(aiogram_user)

        return length, user


class KoroneUserArg(OrArg):
    def __init__(self, *args, allow_unknown_id: bool = False):
        description = args[0] if args else None
        super().__init__(
            KoroneUserMentionArg(),
            KoroneUserIDArg(allow_unknown_id=allow_unknown_id),
            KoroneUsernameArg(),
            description=description,
        )

    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("User: 'User ID (numeric) / Username (starts with @) / Mention (links to users)'"), l_(
            "Users: 'User IDs (numeric) / Usernames (starts with @) / Mentions (links to users)'"
        )

    @property
    def examples(self) -> dict[str | UserLink, LazyProxy | None] | None:
        return {
            "1111224224": l_("User ID"),
            "@ofoxr_bot": l_("Username"),
            UserLink(user_id=1111224224, name="OrangeFox BOT"): l_(
                "A link to user, usually creates by mentioning a user without username."
            ),
        }
