# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>


from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import MessageHandler
from korone.modules.web.utils import parse_whois_output, run_whois
from korone.utils.i18n import gettext as _


class WhoisHandler(MessageHandler):
    @staticmethod
    @router.message(Command("whois"))
    async def handle(client: Client, message: Message) -> None:
        command = CommandObject(message).parse()

        if not command.args:
            await message.reply(
                _("Please provide a domain name to look up. Use /whois &lt;domain&gt;.")
            )
            return

        domain = command.args.split(" ")[0]
        try:
            raw_output = await run_whois(domain)
            parsed_info = parse_whois_output(raw_output)
            if parsed_info:
                text = _("<b>Whois information for {domain}:</b>\n<pre>").format(domain=domain)
                for key, value in parsed_info.items():
                    text += f"<b>{key}</b>: {value}\n"
                text += "</pre>"
                await message.reply(text)
            else:
                await message.reply(
                    _("No whois information found for <code>{domain}</code>.").format(
                        domain=domain
                    )
                )
        except Exception as e:
            await message.reply(
                _("An error occurred while fetching whois information: {error}").format(
                    error=str(e)
                )
            )
