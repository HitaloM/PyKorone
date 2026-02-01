from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Filter
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery
from stfu_tg import Doc, Section, VList

from korone.config import CONFIG
from korone.modules.utils_.admin import check_user_admin_permissions
from korone.modules.utils_.common_try import common_try
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.types import TelegramObject


@dataclass(slots=True)
class UserRestricting(Filter):
    admin: bool = False
    can_post_messages: bool = False
    can_edit_messages: bool = False
    can_delete_messages: bool = False
    can_restrict_members: bool = False
    can_promote_members: bool = False
    can_change_info: bool = False
    can_invite_users: bool = False
    can_pin_messages: bool = False

    ARGUMENTS: dict[str, str] = field(
        default_factory=lambda: {
            "user_admin": "admin",
            "user_can_post_messages": "can_post_messages",
            "user_can_edit_messages": "can_edit_messages",
            "user_can_delete_messages": "can_delete_messages",
            "user_can_restrict_members": "can_restrict_members",
            "user_can_promote_members": "can_promote_members",
            "user_can_change_info": "can_change_info",
            "user_can_invite_users": "can_invite_users",
            "user_can_pin_messages": "can_pin_messages",
        },
        repr=False,
    )
    PAYLOAD_ARGUMENT_NAME: str = field(default="user_member", repr=False)

    required_permissions: list[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.required_permissions = [arg for arg in self.ARGUMENTS.values() if arg != "admin" and getattr(self, arg)]

    @classmethod
    def validate(cls, full_config: dict[str, str | bool]) -> dict[str, str | bool]:
        config: dict[str, str | bool] = {}
        arguments = {
            "user_admin": "admin",
            "user_can_post_messages": "can_post_messages",
            "user_can_edit_messages": "can_edit_messages",
            "user_can_delete_messages": "can_delete_messages",
            "user_can_restrict_members": "can_restrict_members",
            "user_can_promote_members": "can_promote_members",
            "user_can_change_info": "can_change_info",
            "user_can_invite_users": "can_invite_users",
            "user_can_pin_messages": "can_pin_messages",
        }
        for alias, argument in arguments.items():
            if alias in full_config:
                config[argument] = full_config.pop(alias)
        return config

    async def __call__(self, event: TelegramObject) -> bool | dict[str, bool | list[str]]:
        user_tid = await self.get_target_id(event)
        message = event.message if hasattr(event, "message") else event

        chat = getattr(message, "chat", None)
        if chat is None:
            return True

        chat_tid = chat.id

        if chat.type == "private":
            return True

        check = await check_user_admin_permissions(chat_tid, user_tid, self.required_permissions or None)
        if check is not True:
            await self.no_rights_msg(event, required_permissions=check)
            raise SkipHandler

        return True

    async def get_target_id(self, message: TelegramObject) -> int:
        from_user = getattr(message, "from_user", None)
        if from_user is None:
            raise SkipHandler
        return from_user.id

    async def no_rights_msg(self, event: TelegramObject, *, required_permissions: bool | list[str]) -> None:
        if isinstance(event, CallbackQuery):
            if not isinstance(event.message, Message):
                return
            actual_message: Message | CallbackQuery = event.message
        elif isinstance(event, Message):
            actual_message = event
        else:
            return
        is_bot = await self.get_target_id(event) == CONFIG.bot_id

        if not isinstance(required_permissions, bool):
            missing_perms = [p.replace("can_", "").replace("_", " ") for p in required_permissions]
            text = (
                _("I don't have the following permissions to do this:")
                if is_bot
                else _("You don't have the following permissions to do this:")
            )
            doc = Doc(Section(text, VList(*missing_perms)))
        else:
            text = (
                _("I must be an administrator to use this command.")
                if is_bot
                else _("You must be an administrator to use this command.")
            )
            doc = Doc(text)

        async def answer() -> Message:
            return await getattr(actual_message, "answer")(str(doc))

        if hasattr(actual_message, "reply"):
            await common_try(getattr(actual_message, "reply")(str(doc)), reply_not_found=answer)
        elif hasattr(actual_message, "answer"):
            await answer()


class BotHasPermissions(UserRestricting):
    ARGUMENTS: ClassVar[dict[str, str]] = {
        "bot_admin": "admin",
        "bot_can_post_messages": "can_post_messages",
        "bot_can_edit_messages": "can_edit_messages",
        "bot_can_delete_messages": "can_delete_messages",
        "bot_can_restrict_members": "can_restrict_members",
        "bot_can_promote_members": "can_promote_members",
        "bot_can_change_info": "can_change_info",
        "bot_can_invite_users": "can_invite_users",
        "bot_can_pin_messages": "can_pin_messages",
    }
    PAYLOAD_ARGUMENT_NAME = "bot_member"

    async def get_target_id(self, message: TelegramObject) -> int:
        return CONFIG.bot_id
