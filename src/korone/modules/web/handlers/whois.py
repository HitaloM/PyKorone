from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram import flags
from aiogram.filters import Command
from ass_tg.types import WordArg
from stfu_tg import Code, Doc, KeyValue, Template, Title

from korone.modules.web.utils.whois import normalize_domain, parse_whois_output, query_whois
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric


@flags.help(description=l_("Look up WHOIS information for a domain."))
@flags.disableable(name="whois")
class WhoisHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"domain": WordArg(l_("Domain"))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("whois"),)

    async def handle(self) -> None:
        raw_domain = (self.data.get("domain") or "").strip()
        domain = normalize_domain(raw_domain)

        if not domain:
            await self.event.reply(
                Template(
                    _("You should provide a domain name. Example: {example}."), example=Code("/whois example.com")
                ).to_html()
            )
            return

        whois_data = await query_whois(domain)
        if not whois_data:
            await self.event.reply(
                Template(_("No WHOIS information found for {domain}."), domain=Code(domain)).to_html()
            )
            return

        parsed_info = parse_whois_output(whois_data)
        if not parsed_info:
            await self.event.reply(
                Template(_("No WHOIS information found for {domain}."), domain=Code(domain)).to_html()
            )
            return

        doc = Doc(Title(_("WHOIS Information")))
        for key, value in parsed_info.items():
            doc += KeyValue(key, value)

        await self.event.reply(str(doc))
