from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

import aiohttp
import orjson
from aiogram import flags
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.args import ArgumentSchema
from korone.modules.web.args import IPAddressOrDomainArg
from korone.modules.web.callbacks import GetIPCallback, decode_ip, encode_ip
from korone.modules.web.utils.ip import fetch_ip_info
from korone.ui import Code, Italic, UIExpression, field, section, template
from korone.utils.aiohttp_session import HTTPClient
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


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


@dataclass(frozen=True, slots=True)
class IPInfoArguments:
    addresses: tuple[str, ...]


def format_ip_info(ip: str, info: dict[str, Any]) -> UIExpression:
    fields: list[UIExpression] = []
    for key, title in IP_FIELDS.items():
        value = info.get(key)
        if value is None:
            continue
        fields.append(field(str(title), str(value)))

    if "ip" not in info:
        fields.append(field(_("IP"), ip))

    return section(_("IP Information"), *fields)


@flags.help(description=l_("Look up information for an IP address or domain."))
@flags.disableable(name="ip")
class IPInfoHandler(KoroneMessageHandler[IPInfoArguments]):
    IPINFO_URL = "https://ipinfo.io/{target}/json"
    CF_DNS_URL = "https://cloudflare-dns.com/dns-query"

    arguments = ArgumentSchema(IPInfoArguments, addresses=IPAddressOrDomainArg(l_("IP or domain")))

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("ip", "ipinfo"),)

    async def fetch_ip_info(self, ip_or_domain: str) -> dict[str, Any] | None:
        url = self.IPINFO_URL.format(target=ip_or_domain)
        timeout = aiohttp.ClientTimeout(total=15)
        session = await HTTPClient.get_session()
        try:
            async with session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    return None
                data = await response.json(loads=orjson.loads)
                data.pop("readme", None)
                return data
        except aiohttp.ClientError:
            return None

    async def _reply_with_ip_info(self, ip: str) -> None:
        info = await self.fetch_ip_info(ip)
        if not info:
            await self.answer(template(_("No information found for {ip_or_domain}."), ip_or_domain=ip))
            return

        if info.get("bogon"):
            await self.answer(
                template(
                    _(
                        "The provided IP address {ip} is a {bogon} IP address, "
                        "meaning it is either not in use or reserved for special use."
                    ),
                    ip=Code(ip),
                    bogon=Italic("bogon"),
                )
            )
            return

        await self.answer(format_ip_info(ip, info))

    async def handle(self) -> None:
        ips = self.args.addresses

        if len(ips) == 1:
            await self._reply_with_ip_info(ips[0])
            return

        builder = InlineKeyboardBuilder()
        for ip in ips:
            builder.button(text=ip, callback_data=GetIPCallback(ip=encode_ip(ip)))
        builder.adjust(1)

        await self.event.reply(_("Please select an IP address:"), reply_markup=builder.as_markup())


@flags.help(exclude=True)
class IPInfoCallbackHandler(KoroneCallbackQueryHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (GetIPCallback.filter(),)

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = cast("GetIPCallback", self.callback_data)
        ip = decode_ip(callback_data.ip)
        info = await fetch_ip_info(ip)

        if not info:
            await self.edit_text(template(_("No information found for {ip_or_domain}."), ip_or_domain=ip))
            await self.event.answer()
            return

        if info.get("bogon"):
            await self.edit_text(
                template(
                    _(
                        "The provided IP address {ip} is a {bogon} IP address, "
                        "meaning it is either not in use or reserved for special use."
                    ),
                    ip=Code(ip),
                    bogon=Italic("bogon"),
                )
            )
            await self.event.answer()
            return

        await self.edit_text(format_ip_info(ip, info))
        await self.event.answer()
