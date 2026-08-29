from itertools import starmap
from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.args import WordArg, define_arguments
from korone.modules.web.utils.whois import normalize_domain, parse_whois_output, query_whois
from korone.ui import Code, UIExpression, field, section, template
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Look up WHOIS information for a domain."))
@flags.disableable(name="whois")
class WhoisHandler(KoroneMessageHandler):
    arguments = define_arguments(domain=WordArg(l_("Domain")))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("whois"),)

    async def handle(self) -> None:
        raw_domain = (self.data.get("domain") or "").strip()
        domain = normalize_domain(raw_domain)

        if not domain:
            await self.answer(
                template(_("You should provide a domain name. Example: {example}."), example=Code("/whois example.com"))
            )
            return

        whois_data = await query_whois(domain)
        if not whois_data:
            await self.answer(template(_("No WHOIS information found for {domain}."), domain=Code(domain)))
            return

        parsed_info = parse_whois_output(whois_data)
        if not parsed_info:
            await self.answer(template(_("No WHOIS information found for {domain}."), domain=Code(domain)))
            return

        fields: list[UIExpression] = list(starmap(field, parsed_info.items()))
        await self.answer(section(_("WHOIS Information"), *fields))
