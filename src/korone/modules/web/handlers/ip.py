# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.web.callback_data import GetIPCallback
from korone.modules.web.utils import fetch_ip_info, get_ips_from_string
from korone.utils.i18n import gettext as _


@router.message(Command("ip"))
async def ip_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()

    if not command.args:
        await message.reply(
            _(
                "You should provide an IP address or domain name to get information."
                "Example: <code>/ip google.com</code>."
            )
        )
        return

    ips = await get_ips_from_string(command.args.split(" ")[0])
    if not ips:
        await message.reply(
            _("No valid IP addresses or domain names found in the provided input.")
        )
        return

    if len(ips) == 1:
        ip = ips[0]
        info = await fetch_ip_info(ip)
        if not info:
            await message.reply(
                _("No information found for {ip_or_domain}.").format(ip_or_domain=ip)
            )
            return

        if info.get("bogon"):
            await message.reply(
                _(
                    "The provided IP address <code>{ip}</code> is a <i>bogon</i> IP address, "
                    "meaning it is either not in use or is reserved for special use."
                ).format(ip=ip)
            )
            return

        await message.reply(
            "\n".join(f"<b>{key.title()}</b>: <code>{value}</code>" for key, value in info.items())
        )
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=ip, callback_data=GetIPCallback(ip=ip).pack())]
            for ip in ips
        ])

        await message.reply(_("Please select an IP address:"), reply_markup=keyboard)


@router.callback_query(GetIPCallback.filter())
async def handle_ip_callback(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        return

    ip = GetIPCallback.unpack(callback.data).ip
    info = await fetch_ip_info(ip)
    if not info:
        await callback.edit_message_text(
            _("No information found for {ip_or_domain}.").format(ip_or_domain=ip)
        )
        return

    if info.get("bogon"):
        await callback.edit_message_text(
            _(
                "The provided IP address <code>{ip}</code> is a <i>bogon</i> IP address, "
                "meaning it is either not in use or is reserved for special use."
            ).format(ip=ip)
        )
        return

    await callback.edit_message_text(
        text="\n".join(
            f"<b>{key.title()}</b>: <code>{value}</code>" for key, value in info.items()
        )
    )
