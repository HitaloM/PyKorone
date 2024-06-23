# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import CallbackQuery, InlineKeyboardButton, Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import MessageHandler
from korone.handlers.abstract.callback_query_handler import CallbackQueryHandler
from korone.modules.web.callback_data import GetIPCallback
from korone.modules.web.utils import fetch_ip_info, get_ips_from_string
from korone.utils.i18n import gettext as _


class IPInfoHandler(MessageHandler):
    @staticmethod
    @router.message(Command("ip"))
    async def handle(client: Client, message: Message) -> None:
        command = CommandObject(message).parse()

        if not command.args:
            await message.reply(
                _(
                    "Please provide an IP address or domain name to look up. "
                    "Use /ip &lt;ip/domain&gt;"
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
            await IPInfoHandler.reply_with_ip_info(message, ips[0])
        else:
            await IPInfoHandler.reply_with_ip_selection(message, ips)

    @staticmethod
    async def reply_with_ip_info(message: Message, ip: str) -> None:
        try:
            info = await fetch_ip_info(ip)
            if info:
                if info.get("bogon"):
                    await message.reply(IPInfoHandler.format_bogon_message(ip))
                    return

                await message.reply(IPInfoHandler.format_ip_info(info))
            else:
                await message.reply(
                    _("No information found for {ip_or_domain}.").format(ip_or_domain=ip)
                )
        except Exception as e:
            await message.reply(
                _("An error occurred while fetching information: {error}").format(error=str(e))
            )

    @staticmethod
    async def reply_with_ip_selection(message: Message, ips: list) -> None:
        keyboard = InlineKeyboardBuilder()
        for ip in ips:
            keyboard.row(InlineKeyboardButton(text=ip, callback_data=GetIPCallback(ip=ip).pack()))
        await message.reply(_("Please select an IP address:"), reply_markup=keyboard.as_markup())

    @staticmethod
    def format_ip_info(info: dict) -> str:
        if len(info) == 1 and "ip" in info:
            return _("Could not find information for {ip}.").format(ip=info["ip"])

        return "\n".join(
            f"<b>{key.title()}</b>: <code>{value}</code>" for key, value in info.items()
        )

    @staticmethod
    def format_bogon_message(ip: str) -> str:
        return _(
            "The provided IP address <code>{ip}</code> is a <i>bogon</i> IP address, "
            "meaning it is either not in use or is reserved for special use."
        ).format(ip=ip)


class IPInfoCBHandler(CallbackQueryHandler):
    @staticmethod
    @router.callback_query(GetIPCallback.filter())
    async def handle(client: Client, callback: CallbackQuery) -> None:
        if not callback.data:
            return

        ip = GetIPCallback.unpack(callback.data).ip
        info = await fetch_ip_info(ip)
        if info:
            if info.get("bogon"):
                await callback.edit_message_text(IPInfoHandler.format_bogon_message(ip))
                return

            await callback.edit_message_text(text=IPInfoHandler.format_ip_info(info))
