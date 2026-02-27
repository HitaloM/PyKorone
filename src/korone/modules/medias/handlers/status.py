from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.db.repositories.disabling import DisablingRepository
from korone.filters.admin_rights import UserRestricting
from korone.filters.chat_status import GroupChatFilter
from korone.modules.medias.utils.settings import AUTO_DOWNLOAD_KEY, is_auto_download_enabled
from korone.modules.utils_.status_handler import StatusBoolHandlerABC
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Toggle automatic media downloads for this chat."))
@flags.disableable(name="medias")
class MediaAutoDownloadStatus(StatusBoolHandlerABC):
    header_text = l_("Media auto-download")
    change_command = "mediaauto"
    change_args = "on / off"

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("mediaauto"), GroupChatFilter(notify_on_fail=True), UserRestricting(admin=True))

    async def get_status(self) -> bool:
        return await is_auto_download_enabled(self.chat.chat_id)

    async def set_status(self, *, new_status: bool) -> None:
        disabled = await DisablingRepository.get_disabled(self.chat.chat_id)

        if new_status:
            if AUTO_DOWNLOAD_KEY not in disabled:
                return
            disabled = [cmd for cmd in disabled if cmd != AUTO_DOWNLOAD_KEY]
            await DisablingRepository.set_disabled(self.chat.chat_id, disabled)
            return

        if AUTO_DOWNLOAD_KEY in disabled:
            return

        await DisablingRepository.set_disabled(self.chat.chat_id, [*disabled, AUTO_DOWNLOAD_KEY])
