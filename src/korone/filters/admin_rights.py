from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import Filter
from aiogram.types import Message
from aiogram.types.callback_query import CallbackQuery
from stfu_tg import Doc, Section, VList

from korone.config import CONFIG
from korone.constants import TELEGRAM_ANONYMOUS_ADMIN_BOT_ID
from korone.db.repositories.chat import ChatRepository
from korone.db.repositories.chat_admin import ChatAdminRepository
from korone.modules.utils_.admin import check_user_admin_permissions
from korone.modules.utils_.common_try import common_try
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.types import TelegramObject

    from korone.db.models.chat import ChatModel


@dataclass(slots=True)
class UserRestricting(Filter):
    admin: bool = False
    user_owner: bool = False
    can_post_messages: bool = False
    can_edit_messages: bool = False
    can_delete_messages: bool = False
    can_restrict_members: bool = False
    can_promote_members: bool = False
    can_change_info: bool = False
    can_invite_users: bool = False
    can_pin_messages: bool = False

    ARGUMENTS: ClassVar[dict[str, str]] = {
        "user_admin": "admin",
        "user_owner": "user_owner",
        "user_can_post_messages": "can_post_messages",
        "user_can_edit_messages": "can_edit_messages",
        "user_can_delete_messages": "can_delete_messages",
        "user_can_restrict_members": "can_restrict_members",
        "user_can_promote_members": "can_promote_members",
        "user_can_change_info": "can_change_info",
        "user_can_invite_users": "can_invite_users",
        "user_can_pin_messages": "can_pin_messages",
    }
    PAYLOAD_ARGUMENT_NAME: ClassVar[str] = "user_member"

    required_permissions: list[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.required_permissions = [
            arg for arg in self.ARGUMENTS.values() if arg not in {"admin", "user_owner"} and getattr(self, arg)
        ]

    @classmethod
    def validate(cls, full_config: dict[str, str | bool]) -> dict[str, str | bool]:
        config: dict[str, str | bool] = {}
        arguments = {
            "user_admin": "admin",
            "user_owner": "user_owner",
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
        self, event: TelegramObject, chat_db: ChatModel | None = None, user_db: ChatModel | None = None
    ) -> bool | dict[str, Any]:
        user_id = await self.get_target_id(event)
        payload: dict[str, Any] = {}

        if isinstance(event, CallbackQuery):
            message = event.message
        elif isinstance(event, Message):
            message = event
        else:
            return True

        if message is None:
            return True

        chat = getattr(message, "chat", None)
        if chat is None:
            return True

        chat_id = chat.id
        if chat.type == ChatType.PRIVATE:
            return True

        anonymous_resolution = await self.resolve_anonymous_admin_permissions(
            event=event, chat_id=chat_id, user_id=user_id, chat_db=chat_db, user_db=user_db
        )
        if anonymous_resolution:
            if anonymous_resolution.permission_check is not True:
                if not anonymous_resolution.already_notified:
                    if self.user_owner:
                        await self.no_owner_msg(event)
                    else:
                        await self.no_rights_msg(event, required_permissions=anonymous_resolution.permission_check)
                raise SkipHandler

            if anonymous_resolution.resolved_user_db:
                payload["user_db"] = anonymous_resolution.resolved_user_db

            return payload or True

        if self.user_owner:
            is_owner = await check_user_admin_permissions(
                chat_id, user_id, require_creator=True, chat_model=chat_db, user_model=user_db
            )
            if is_owner is not True:
                await self.no_owner_msg(event)
                raise SkipHandler
            return True

        check = await check_user_admin_permissions(
            chat_id, user_id, self.required_permissions or None, chat_model=chat_db, user_model=user_db
        )
        if check is not True:
            await self.no_rights_msg(event, required_permissions=check)
            raise SkipHandler

        return payload or True

    async def resolve_anonymous_admin_permissions(
        self, event: TelegramObject, chat_id: int, user_id: int, chat_db: ChatModel | None, user_db: ChatModel | None
    ) -> AnonymousResolution | None:
        if user_id != TELEGRAM_ANONYMOUS_ADMIN_BOT_ID:
            return None

        message: Any = event.message if isinstance(event, CallbackQuery) else event
        sender_chat = getattr(message, "sender_chat", None)
        if not sender_chat or sender_chat.id != chat_id:
            return None

        title = getattr(message, "author_signature", None)
        if not title:
            await self.no_anon_title_msg(event)
            return AnonymousResolution(permission_check=False, resolved_user_db=None, already_notified=True)

        if chat_db is None:
            chat_db = await ChatRepository.get_by_chat_id(chat_id)

        if chat_db is None:
            return AnonymousResolution(permission_check=False, resolved_user_db=None)

        admins = await ChatAdminRepository.get_chat_admins(chat_db)
        matched_admins = []
        for admin in admins:
            member_is_anonymous = bool(admin.data.get("is_anonymous", False))
            member_custom_title = admin.data.get("custom_title")
            if member_is_anonymous and member_custom_title == title:
                matched_admins.append(admin)

        if not matched_admins:
            await self.no_anon_title_match_msg(event)
            return AnonymousResolution(permission_check=False, resolved_user_db=None, already_notified=True)

        checks = [
            self.check_member_permissions(member_data=admin.data, require_creator=self.user_owner)
            for admin in matched_admins
        ]
        if not all(check is True for check in checks):
            await self.no_anon_ambiguous_msg(event)
            return AnonymousResolution(permission_check=False, resolved_user_db=None, already_notified=True)

        if len(matched_admins) == 1:
            resolved_user_db = await ChatRepository.get_by_id(matched_admins[0].user_id)
            if resolved_user_db:
                return AnonymousResolution(permission_check=True, resolved_user_db=resolved_user_db)

        if user_db and user_db.chat_id != TELEGRAM_ANONYMOUS_ADMIN_BOT_ID:
            return AnonymousResolution(permission_check=True, resolved_user_db=user_db)

        for admin in matched_admins:
            resolved_user_db = await ChatRepository.get_by_id(admin.user_id)
            if resolved_user_db:
                return AnonymousResolution(permission_check=True, resolved_user_db=resolved_user_db)

        return AnonymousResolution(permission_check=True, resolved_user_db=None)

    def check_member_permissions(
        self, member_data: dict[str, Any], *, require_creator: bool = False
    ) -> bool | list[str]:
        if require_creator:
            return self._is_creator_status(member_data.get("status"))

        if self._is_creator_status(member_data.get("status")):
            return True

        if not self.required_permissions:
            return True

        missing_permissions = []
        for permission in self.required_permissions:
            permission_value = member_data.get(permission)
            if permission_value is not True:
                missing_permissions.append(permission)

        return missing_permissions or True

    @staticmethod
    def _is_creator_status(status: str | ChatMemberStatus | None) -> bool:
        try:
            return ChatMemberStatus(status) == ChatMemberStatus.CREATOR
        except TypeError, ValueError:
            return False

    @staticmethod
    async def get_target_id(message: TelegramObject) -> int:
        from_user = getattr(message, "from_user", None)
        if from_user is None:
            raise SkipHandler
        return from_user.id

    async def no_rights_msg(self, event: TelegramObject, *, required_permissions: bool | list[str]) -> None:
        if not isinstance(event, (CallbackQuery, Message)):
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

        if isinstance(event, CallbackQuery):
            await event.answer(str(doc), show_alert=True)
            return

        async def answer() -> Message:
            return await event.answer(str(doc))

        if hasattr(event, "reply"):
            await common_try(event.reply(str(doc)), reply_not_found=answer)
        elif hasattr(event, "answer"):
            await answer()

    async def no_anon_title_msg(self, event: TelegramObject) -> None:
        await self.send_doc(event, Doc(_("Anonymous admin must have a custom admin title to use this command.")))

    async def no_anon_title_match_msg(self, event: TelegramObject) -> None:
        await self.send_doc(
            event, Doc(_("Could not resolve this anonymous admin title. Refresh admin cache or use a unique title."))
        )

    async def no_anon_ambiguous_msg(self, event: TelegramObject) -> None:
        await self.send_doc(
            event,
            Doc(
                _(
                    "Multiple anonymous admins share this title, and not all of them can use this command. "
                    "Use a unique title."
                )
            ),
        )

    async def no_owner_msg(self, event: TelegramObject) -> None:
        await self.send_doc(event, Doc(_("You must be the chat creator to use this command.")))

    @staticmethod
    async def send_doc(event: TelegramObject, doc: Doc) -> None:
        if isinstance(event, CallbackQuery):
            await event.answer(str(doc), show_alert=True)
            return

        if not isinstance(event, Message):
            return

        async def answer() -> Message:
            return await event.answer(str(doc))

        if hasattr(event, "reply"):
            await common_try(event.reply(str(doc)), reply_not_found=answer)
        elif hasattr(event, "answer"):
            await answer()


@dataclass(slots=True)
class AnonymousResolution:
    permission_check: bool | list[str]
    resolved_user_db: ChatModel | None
    already_notified: bool = False


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

    @staticmethod
    async def get_target_id(message: TelegramObject) -> int:
        return CONFIG.bot_id
