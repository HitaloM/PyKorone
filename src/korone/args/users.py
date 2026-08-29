from typing import TYPE_CHECKING, override

from korone.args.base import (
    Argument,
    ArgumentDescription,
    ArgumentEntities,
    ArgumentExamples,
    ArgumentTypeError,
    ArgumentValueError,
    ParsedArgument,
)
from korone.args.types import OrArg
from korone.db.models.chat import ChatModel
from korone.db.repositories.chat import ChatRepository
from korone.ui import mention
from korone.ui.rendering import plain_text
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from korone.utils.i18n import LazyProxy


class KoroneUserIDArg(Argument[ChatModel]):
    __slots__ = ("allow_unknown_id",)

    def __init__(self, description: ArgumentDescription | None = None, *, allow_unknown_id: bool = False) -> None:
        super().__init__(description)
        self.allow_unknown_id = allow_unknown_id

    @override
    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("User ID (Numeric)"), l_("User IDs (Numeric)")

    async def parse(self, text: str, entities: ArgumentEntities) -> ParsedArgument[ChatModel]:
        del entities
        raw_user_id = text.split(maxsplit=1)[0] if text.strip() else ""
        if not raw_user_id.lstrip("-").isdigit():
            raise ArgumentTypeError
        user_id = int(raw_user_id)

        try:
            user = await ChatRepository.find_user(user_id)
        except LookupError:
            if not self.allow_unknown_id:
                raise ArgumentValueError(_("Could not find the requested User ID in the database."))
            user = ChatModel.user_from_id(user_id)
        else:
            return ParsedArgument(length=len(raw_user_id), value=user)
        return ParsedArgument(length=len(raw_user_id), value=user)


class KoroneUsernameArg(Argument[ChatModel]):
    __slots__ = ()

    prefix: str = "@"

    @override
    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("Username (starts with @)"), l_("Usernames (starts with @)")

    async def parse(self, text: str, entities: ArgumentEntities) -> ParsedArgument[ChatModel]:
        del entities
        raw_username = text.split(maxsplit=1)[0] if text.strip() else ""
        if not raw_username.startswith(self.prefix):
            raise ArgumentTypeError
        username = raw_username.removeprefix(self.prefix)

        try:
            user = await ChatRepository.find_user_by_username(username)
        except LookupError:
            raise ArgumentValueError(_("Could not find the requested Username in the database."))
        else:
            return ParsedArgument(length=len(raw_username), value=user)


class KoroneUserMentionArg(Argument[ChatModel]):
    __slots__ = ()

    _allowed_entities = ("mention", "text_mention")

    @override
    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("User mention"), l_("User mentions")

    async def parse(self, text: str, entities: ArgumentEntities) -> ParsedArgument[ChatModel]:
        entity = next(
            (entity for entity in entities if entity.offset == 0 and entity.type in self._allowed_entities), None
        )
        if entity is None:
            raise ArgumentTypeError

        if entity.type == "text_mention" and entity.user is not None:
            aiogram_user = entity.user
        else:
            username = text[: entity.length].lstrip("@")
            try:
                user = await ChatRepository.find_user_by_username(username)
            except LookupError:
                raise ArgumentValueError(_("Could not find the mentioned user in the database."))
            else:
                return ParsedArgument(length=entity.length, value=user)

        try:
            user = await ChatRepository.find_user(aiogram_user.id)
        except LookupError:
            user = await ChatRepository.upsert_user(aiogram_user)

        return ParsedArgument(length=entity.length, value=user)


class KoroneUserArg(OrArg[ChatModel]):
    def __init__(self, description: ArgumentDescription | None = None, *, allow_unknown_id: bool = False) -> None:
        super().__init__(
            KoroneUserMentionArg(),
            KoroneUserIDArg(allow_unknown_id=allow_unknown_id),
            KoroneUsernameArg(),
            description=description,
        )

    @override
    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("User: 'User ID (numeric) / Username (starts with @) / Mention (links to users)'"), l_(
            "Users: 'User IDs (numeric) / Usernames (starts with @) / Mentions (links to users)'"
        )

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {
            "1111224224": l_("User ID"),
            "@ofoxr_bot": l_("Username"),
            plain_text(mention(1111224224, "OrangeFox BOT")): l_(
                "A link to user, usually creates by mentioning a user without username."
            ),
        }
