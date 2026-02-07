from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags

from korone.filters.admin_rights import UserRestricting
from korone.filters.chat_status import GroupChatFilter
from korone.filters.cmd import CMDFilter
from korone.modules.medias.utils.settings import is_auto_download_enabled, set_auto_download_enabled
from korone.modules.utils_.status_handler import StatusBoolHandlerABC
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Enable or disable automatic media downloads in this chat."))
@flags.disableable(name="medias")
class MediaAutoDownloadStatus(StatusBoolHandlerABC):
    header_text = l_("Media auto-download")
    change_command = "mediaauto"
    change_args = l_("on / off")

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("mediaauto"), GroupChatFilter(notify_on_fail=True), UserRestricting(admin=True))

    async def get_status(self) -> bool:
        return await is_auto_download_enabled(self.chat.chat_id)

    async def set_status(self, *, new_status: bool) -> None:
        await set_auto_download_enabled(self.chat.chat_id, enabled=new_status)
