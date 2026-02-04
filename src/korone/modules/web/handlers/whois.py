from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags
from ass_tg.types import WordArg
from stfu_tg import Doc, KeyValue, Title

from korone.filters.cmd import CMDFilter
from korone.logging import get_logger
from korone.modules.web.utils import normalize_domain, parse_whois_output, run_whois
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric

    from korone.utils.handlers import HandlerData

logger = get_logger(__name__)


@flags.help(description=l_("Shows WHOIS information about a domain."))
@flags.disableable(name="whois")
class WhoisHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: HandlerData) -> dict[str, ArgFabric]:
        return {"domain": WordArg(l_("Domain"))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("whois"),)

    async def handle(self) -> None:
        raw_domain = (self.data.get("domain") or "").strip()
        domain = normalize_domain(raw_domain)

        if not domain:
            await self.event.reply(_("You should provide a domain name. Example: <code>/whois example.com</code>."))
            return

        raw_output = await run_whois(domain)
        parsed_info = parse_whois_output(raw_output)

        if not parsed_info:
            await self.event.reply(_("No WHOIS information found for <code>{domain}</code>.").format(domain=domain))
            return

        doc = Doc(Title(_("WHOIS Information")))
        for key, value in parsed_info.items():
            doc += KeyValue(key, value)

        await self.event.reply(str(doc))
