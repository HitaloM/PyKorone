from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from aiogram import flags
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ass_tg.types import TextArg
from stfu_tg import Doc, KeyValue, Title

from korone.filters.cmd import CMDFilter
from korone.modules.web.callbacks import GetIPCallback, decode_ip, encode_ip
from korone.modules.web.utils import fetch_ip_info, get_ips_from_string
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from ass_tg.types.base_abc import ArgFabric

    from korone.utils.handlers import HandlerData

IP_FIELDS = {
    "ip": l_("IP"),
    "hostname": l_("Hostname"),
    "city": l_("City"),
    "region": l_("Region"),
    "country": l_("Country"),
    "loc": l_("Location"),
    "org": l_("Organization"),
    "postal": l_("Postal"),
    "timezone": l_("Timezone"),
}


@flags.help(description=l_("Shows information about an IP or domain."))
@flags.disableable(name="ip")
class IPInfoHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: HandlerData) -> dict[str, ArgFabric]:
        return {"target": TextArg(l_("IP or domain"))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("ip", "ipinfo")),)

    async def handle(self) -> None:
        target = (self.data.get("target") or "").strip()

        if not target:
            await self.event.reply(
                _("You should provide an IP address or domain. Example: <code>/ip google.com</code>.")
            )
            return

        ips = await get_ips_from_string(target)
        if not ips:
            await self.event.reply(_("No valid IP addresses or domains found in the provided input."))
            return

        if len(ips) == 1:
            await self._reply_with_ip_info(ips[0])
            return

        builder = InlineKeyboardBuilder()
        for ip in ips:
            builder.row(InlineKeyboardButton(text=ip, callback_data=GetIPCallback(ip=encode_ip(ip)).pack()))

        await self.event.reply(_("Please select an IP address:"), reply_markup=builder.as_markup())

    async def _reply_with_ip_info(self, ip: str) -> None:
        info = await fetch_ip_info(ip)
        if not info:
            await self.event.reply(_("No information found for {ip_or_domain}.").format(ip_or_domain=ip))
            return

        if info.get("bogon"):
            await self.event.reply(
                _(
                    "The provided IP address <code>{ip}</code> is a <i>bogon</i> IP address, "
                    "meaning it is either not in use or reserved for special use."
                ).format(ip=ip)
            )
            return

        await self.event.reply(str(format_ip_info(ip, info)))


@flags.help(exclude=True)
class IPInfoCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (GetIPCallback.filter(),)

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = cast("GetIPCallback", self.callback_data)
        ip = decode_ip(callback_data.ip)
        info = await fetch_ip_info(ip)

        if not info:
            await self.edit_text(_("No information found for {ip_or_domain}.").format(ip_or_domain=ip))
            await self.event.answer()
            return

        if info.get("bogon"):
            await self.edit_text(
                _(
                    "The provided IP address <code>{ip}</code> is a <i>bogon</i> IP address, "
                    "meaning it is either not in use or reserved for special use."
                ).format(ip=ip)
            )
            await self.event.answer()
            return

        await self.edit_text(str(format_ip_info(ip, info)))
        await self.event.answer()


def format_ip_info(ip: str, info: dict[str, Any]) -> Doc:
    doc = Doc(Title(_("IP Information")))

    for key, title in IP_FIELDS.items():
        value = info.get(key)
        if value is None:
            continue
        doc += KeyValue(str(title), str(value))

    if "ip" not in info:
        doc += KeyValue(_("IP"), ip)

    return doc
