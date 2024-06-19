from dataclasses import dataclass
from typing import Any, Union

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Filter
from aiogram.types import TelegramObject
from aiogram.types.callback_query import CallbackQuery

from sophie_bot import CONFIG
from sophie_bot.modules.legacy_modules.utils.language import get_strings
from sophie_bot.modules.legacy_modules.utils.user_details import check_admin_rights


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

    ARGUMENTS = {
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
    PAYLOAD_ARGUMENT_NAME = "user_member"

    def __post_init__(self):
        self.required_permissions = {
            arg: True for arg in self.ARGUMENTS.values() if getattr(self, arg)
        }

    @classmethod
    def validate(cls, full_config):
        config = {}
        for alias, argument in cls.ARGUMENTS.items():
            if alias in full_config:
                config[argument] = full_config.pop(alias)
        return config

    async def __call__(self, event: TelegramObject) -> Union[bool, dict[str, Any]]:
        user_id = await self.get_target_id(event)
        message = event.message if hasattr(event, 'message') else event

        # If pm skip checks
        if message.chat.type == 'private':
            return True

        check = await check_admin_rights(message, message.chat.id, user_id, self.required_permissions.keys())
        if check is not True:
            # check = missing permission in this scope
            await self.no_rights_msg(event, check)
            return False

        return True

    async def get_target_id(self, message):
        return message.from_user.id

    async def no_rights_msg(self, message, required_permissions):
        strings = await get_strings(message.message.chat.id if hasattr(message, 'message')
                                    else message.chat.id, 'global')
        task = message.answer if hasattr(message, 'message') else message.reply
        if not isinstance(required_permissions, bool):  # Check if check_admin_rights func returned missing perm
            required_permissions = ' '.join(required_permissions.strip('can_').split('_'))
            try:
                await task(strings['user_no_right'].format(permission=required_permissions))
            except TelegramBadRequest as error:
                if error.args == 'Reply message not found':
                    return await message.answer(strings['user_no_right'])
        else:
            try:
                await task(strings['user_no_right:not_admin'])
            except TelegramBadRequest as error:
                if error.args == 'Reply message not found':
                    return await message.answer(strings['user_no_right:not_admin'])


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

    async def get_target_id(self, message):
        return CONFIG.bot_id

    async def no_rights_msg(self, message, required_permissions):
        message = message.message if isinstance(message, CallbackQuery) else message
        strings = await get_strings(message.chat.id, 'global')
        if not isinstance(required_permissions, bool):
            required_permissions = ' '.join(required_permissions.strip('can_').split('_'))
            try:
                await message.reply(strings['bot_no_right'].format(permission=required_permissions))
            except TelegramBadRequest as error:
                if error.args == 'Reply message not found':
                    return await message.answer(strings['bot_no_right'])
        else:
            try:
                await message.reply(strings['bot_no_right:not_admin'])
            except TelegramBadRequest as error:
                if error.args == 'Reply message not found':
                    return await message.answer(strings['bot_no_right:not_admin'])
