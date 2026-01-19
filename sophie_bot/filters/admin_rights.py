from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union

from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Filter
from aiogram.types import TelegramObject
from aiogram.types.callback_query import CallbackQuery
from stfu_tg import Doc, Section, VList

from sophie_bot.config import CONFIG
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.utils_.admin import check_user_admin_permissions
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log


@dataclass
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
    def validate(cls, full_config: dict[str, Any]) -> dict[str, Any]:
        config: dict[str, Any] = {}
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

    async def __call__(
        self, event: TelegramObject, connection: Optional[ChatConnection] = None
    ) -> Union[bool, dict[str, Any]]:
        user_tid = await self.get_target_id(event)
        message = event.message if hasattr(event, "message") else event

        chat_tid = connection.tid if connection else message.chat.id  # type: ignore[union-attr]
        is_connected = connection.is_connected if connection else False

        # Skip if in PM and not connected to the chat
        if not is_connected and message.chat.type == "private":  # type: ignore[union-attr]
            log.debug("Admin rights: Private message without connection")
            return True

        elif is_connected:
            log.debug("Admin rights: Connection to the chat detected")

        check = await check_user_admin_permissions(chat_tid, user_tid, self.required_permissions or None)
        if check is not True:
            # check = missing permission in this scope
            await self.no_rights_msg(event, check)
            raise SkipHandler

        return True

    async def get_target_id(self, message: TelegramObject) -> int:
        return message.from_user.id  # type: ignore[union-attr]

    async def no_rights_msg(self, event: TelegramObject, required_permissions: Union[bool, list[str]]) -> None:
        actual_message: Any = event.message if isinstance(event, CallbackQuery) else event
        is_bot = await self.get_target_id(event) == CONFIG.bot_id

        if not isinstance(required_permissions, bool):  # Check if check_user_admin_permissions returned missing perm
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

        async def answer() -> Any:
            return await getattr(actual_message, "answer")(str(doc))

        if hasattr(actual_message, "reply"):
            await common_try(getattr(actual_message, "reply")(str(doc)), reply_not_found=answer)
        elif hasattr(actual_message, "answer"):
            await answer()


class BotHasPermissions(UserRestricting):
    ARGUMENTS = {
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
