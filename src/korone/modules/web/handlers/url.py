from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import flags
from aiogram.filters import Command
from ass_tg.types import TextArg
from stfu_tg import Code, Doc, KeyValue, Template, Title

from korone.modules.web.utils.misc import normalize_url
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric


@flags.help(description=l_("Normalize a URL."))
@flags.disableable(name="url")
class URLNormalizeHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"url": TextArg(l_("URL"))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("url"),)

    async def handle(self) -> None:
        raw_url = (self.data.get("url") or "").strip()

        if not raw_url:
            await self.event.reply(
                Template(
                    _("You should provide a URL. Example: {example}."),
                    example=Code("/url example.com/path?utm_source=test#section"),
                ).to_html()
            )
            return

        normalized = normalize_url(raw_url)
        if not normalized:
            await self.event.reply(Template(_("I couldn't normalize this URL: {url}"), url=Code(raw_url)).to_html())
            return

        if normalized == raw_url:
            await self.event.reply(Template(_("This URL is already normalized: {url}"), url=Code(raw_url)).to_html())
            return

        doc = Doc(Title(_("URL Normalization")))
        doc += KeyValue(_("Input"), Code(raw_url))
        doc += KeyValue(_("Normalized"), Code(normalized))
        await self.event.reply(str(doc))
