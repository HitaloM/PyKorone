# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.web.utils import parse_whois_output, run_whois
from korone.utils.i18n import gettext as _


@router.message(Command("whois"))
async def whois_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()

    if not command.args:
        await message.reply(
            _(
                "You should provide a domain name to get whois information. "
                "Example: <code>/whois google.com</code>."
            )
        )
        return

    domain = command.args.split(" ")[0]

    try:
        raw_output = await run_whois(domain)
        parsed_info = parse_whois_output(raw_output)
    except Exception as e:
        await message.reply(
            _("An error occurred while fetching whois information: {error}").format(error=str(e))
        )
        return

    if not parsed_info:
        await message.reply(
            _("No whois information found for <code>{domain}</code>.").format(domain=domain)
        )
        return

    text = "".join(f"<b>{key}</b>: <code>{value}</code>\n" for key, value in parsed_info.items())
    await message.reply(text)
