from typing import TYPE_CHECKING, override

from aiogram.types import User

from korone.args import (
    Argument,
    ArgumentDescription,
    ArgumentExamples,
    ArgumentSource,
    ArgumentTypeError,
    ArgumentValueError,
    OrArg,
    ParsedArgument,
)
from korone.db.models.chat import ChatModel
from korone.db.repositories.chat import ChatRepository
from korone.ui import TextMention
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from korone.utils.i18n import LazyProxy


class UserIDArg(Argument[ChatModel]):
    __slots__ = ("allow_unknown_id",)

    def __init__(self, description: ArgumentDescription | None = None, *, allow_unknown_id: bool = False) -> None:
        super().__init__(description)
        self.allow_unknown_id = allow_unknown_id

    @override
    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("User ID (Numeric)"), l_("User IDs (Numeric)")

    @override
    async def parse(self, source: ArgumentSource) -> ParsedArgument[ChatModel]:
        raw_user_id = source.text.split(maxsplit=1)[0] if source.text else ""
        if not raw_user_id.lstrip("-").isdigit():
            raise ArgumentTypeError
        user_id = int(raw_user_id)

        try:
            user = await ChatRepository.find_user(user_id)
        except LookupError:
            if not self.allow_unknown_id:
                raise ArgumentValueError(_("Could not find the requested User ID in the database."))
            user = ChatModel.user_from_id(user_id)

        return ParsedArgument(consumed=len(raw_user_id), value=user)


class UsernameArg(Argument[ChatModel]):
    __slots__ = ()

    prefix = "@"

    @override
    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("Username (starts with @)"), l_("Usernames (starts with @)")

    @override
    async def parse(self, source: ArgumentSource) -> ParsedArgument[ChatModel]:
        raw_username = source.text.split(maxsplit=1)[0] if source.text else ""
        if not raw_username.startswith(self.prefix):
            raise ArgumentTypeError
        username = raw_username.removeprefix(self.prefix)

        try:
            user = await ChatRepository.find_user_by_username(username)
        except LookupError:
            raise ArgumentValueError(_("Could not find the requested Username in the database."))

        return ParsedArgument(consumed=len(raw_username), value=user)


class UserMentionArg(Argument[ChatModel]):
    __slots__ = ()

    _allowed_entities = frozenset({"mention", "text_mention"})

    @override
    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("User mention"), l_("User mentions")

    @override
    async def parse(self, source: ArgumentSource) -> ParsedArgument[ChatModel]:
        entity = next(
            (entity for entity in source.entities if entity.offset == 0 and entity.type in self._allowed_entities), None
        )
        if entity is None:
            raise ArgumentTypeError

        if entity.type == "text_mention" and entity.user is not None:
            try:
                user = await ChatRepository.find_user(entity.user.id)
            except LookupError:
                user = await ChatRepository.upsert_user(entity.user)
            return ParsedArgument(consumed=entity.length, value=user)

        username = source.text[: entity.length].lstrip("@")
        try:
            user = await ChatRepository.find_user_by_username(username)
        except LookupError:
            raise ArgumentValueError(_("Could not find the mentioned user in the database."))

        return ParsedArgument(consumed=entity.length, value=user)


class UserArg(OrArg[ChatModel]):
    def __init__(self, description: ArgumentDescription | None = None, *, allow_unknown_id: bool = False) -> None:
        super().__init__(
            UserMentionArg(), UserIDArg(allow_unknown_id=allow_unknown_id), UsernameArg(), description=description
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
            "777000": l_("User ID"),
            "@SpamBot": l_("Username"),
            TextMention(
                "Telegram Notifications", user=User(id=777000, is_bot=False, first_name="Telegram Notifications")
            ): l_("User mention"),
        }
