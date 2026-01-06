from datetime import datetime
from types import ModuleType
from typing import Any

from aiogram import flags
from aiogram.handlers import BaseHandler
from aiogram.types import BufferedInputFile, Message
from ujson import dumps

from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_

VERSION = 6

EXPORTABLE_MODULES: list[ModuleType] = []


def text_to_buffered_file(text: str, filename: str = "data.txt") -> BufferedInputFile:
    return BufferedInputFile(text.encode(), filename=filename)


@flags.help(description=l_("Exports your data to a JSON file"))
class TriggerExport(BaseHandler[Message]):
    @staticmethod
    async def get_data(chat_id: int) -> list[dict[str, Any]]:
        return list(
            filter(
                None,
                [await module.__export__(chat_id) for module in EXPORTABLE_MODULES if hasattr(module, "__export__")],
            )
        )

    async def handle(self) -> Any:
        connection: ChatConnection = self.data["connection"]

        await self.event.reply(_("Export is started, this may take a while."))

        data = self.get_initial_data(connection)
        modules_data = await self.get_data(connection.tid)

        for module_data in modules_data:
            data.update(module_data)

        jfile = text_to_buffered_file(dumps(data, indent=2))
        text = _("Export is done.")
        await self.event.reply_document(jfile, caption=text)

    @staticmethod
    def get_initial_data(connection: ChatConnection) -> dict[str, Any]:
        return {
            "general": {
                "chat_name": connection.title,
                "chat_id": connection.tid,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": VERSION,
            }
        }
