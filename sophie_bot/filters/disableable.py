from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Filter
from aiogram.types import Message

from sophie_bot.modules.legacy_modules.utils.disable import LEGACY_DISABLABLE_COMMANDS
from sophie_bot.modules.legacy_modules.utils.user_details import is_user_admin
from sophie_bot.services.db import db
from sophie_bot.utils.logger import log


class DisableableCMD(Filter):
    def __init__(self, command: str):
        log.debug(f"DisableableCMD: Adding {command} to the disableable commands...")

        self.command = command

        if command not in LEGACY_DISABLABLE_COMMANDS:
            LEGACY_DISABLABLE_COMMANDS.append(command)

    async def __call__(self, message: Message) -> bool:
        # TODO: Refactor legacy code here
        chat_id = message.chat.id

        if not message.from_user:
            # No user?
            return True

        user_id = message.from_user.id

        check = await db.disabled.find_one({"chat_id": chat_id, "cmds": {"$in": [self.command]}})
        if check and not await is_user_admin(chat_id, user_id):
            # Disabled
            raise SkipHandler
        elif check:
            log.debug(f"User {user_id} is admin, ignoring disableable command {self.command}")
        return True
