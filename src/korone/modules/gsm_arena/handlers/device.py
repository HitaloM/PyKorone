# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import urllib.parse
from contextlib import suppress
from dataclasses import dataclass
from datetime import timedelta

import httpx
from bs4 import BeautifulSoup
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from korone import cache
from korone.client import Korone
from korone.config import ConfigManager
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.handlers.message_handler import MessageHandler
from korone.modules.gsm_arena.callback_data import DevicePageCallback, GetDeviceCallback
from korone.modules.utils.commands import get_command_arg
from korone.modules.utils.pagination import Pagination
from korone.utils.i18n import gettext as _

CMDS: list[str] = ["device", "specs", "d"]

HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "referer": "https://www.gsmarena.com/",
}


@dataclass
class PhoneSearchResult:
    name: str
    url: str


def parse_specs(specs_data: dict) -> dict:
    data = {}
    details = specs_data.get("specs", {})
    data["name"] = specs_data.get("name")
    data["url"] = specs_data.get("url")
    data["status"] = details.get("Launch", [{}]).get("Status")
    data["network"] = details.get("Network", [{}]).get("Technology")
    data["weight"] = details.get("Body", [{}]).get("Weight")

    display = details.get("Display", [{}])
    data["display"] = (
        f"{display.get('Type', '')}\n{display.get('Size', '')}\n{display.get('Resolution', '')}"
    )

    platform = details.get("Platform", [{}])
    data["chipset"] = (
        f"{platform.get('Chipset', '')}\n{platform.get('CPU', '')}\n{platform.get('GPU', '')}"
    )

    data["memory"] = details.get("Memory", [{}]).get("Internal")

    main_cam = details.get("Main Camera", [{}])
    camera = next(iter(main_cam.items()), (None, None))
    data["main_camera"] = f"{camera[0]} {camera[1]}" if camera[0] and camera[1] else None

    front_cam = details.get("Selfie camera", [{}])
    camera = next(iter(front_cam.items()), (None, None))
    data["selfie_camera"] = f"{camera[0]} {camera[1]}" if camera[0] and camera[1] else None

    data["jack"] = details.get("Sound", [{}]).get("3.5mm jack")
    data["usb"] = details.get("Comms", [{}]).get("USB")
    data["sensors"] = details.get("Features", [{}]).get("Sensors")
    data["battery"] = details.get("Battery", [{}]).get("Type")
    data["charging"] = details.get("Battery", [{}]).get("Charging")

    return data


def format_phone(phone: dict) -> str:
    phone = parse_specs(phone)
    attributes_dict = {
        _("Status"): "status",
        _("Network"): "network",
        _("Weight"): "weight",
        _("Display"): "display",
        _("Chipset"): "chipset",
        _("Memory"): "memory",
        _("Rear Camera"): "main_camera",
        _("Front Camera"): "selfie_camera",
        _("3.5mm jack"): "jack",
        _("USB"): "usb",
        _("Sensors"): "sensors",
        _("Battery"): "battery",
        _("Charging"): "charging",
    }

    attributes = [
        f"<b>{key}:</b> {phone[value]}"
        for key, value in attributes_dict.items()
        if phone[value] is not None
    ]

    return f"<a href='{phone['url']}'>{phone['name']}</a>\n\n{'\n\n'.join(attributes)}"


def create_pagination_layout(devices: list, query: str, page: int) -> InlineKeyboardBuilder:
    layout = Pagination(
        devices,
        item_data=lambda i, _: GetDeviceCallback(device=i.url).pack(),
        item_title=lambda i, _: i.name,
        page_data=lambda pg: DevicePageCallback(device=query, page=pg).pack(),
    )

    return layout.create(page, lines=8)


def not_too_many_requests(result, args, kwargs, key=None) -> bool:
    return result and "Too Many Requests" not in result.text


class GSMArena(MessageHandler):
    @staticmethod
    @cache(ttl=timedelta(weeks=3), condition=not_too_many_requests)
    async def fetch_and_parse(url: str, proxy: str | None = None) -> BeautifulSoup:
        async with httpx.AsyncClient(http2=True, proxy=proxy) as client:
            response = await client.get(
                f"https://cors-bypass.amano.workers.dev/{url}", headers=HEADERS
            )
            html = response.content

            return BeautifulSoup(html, "lxml")

    async def fetch_with_retry(self, url: str) -> BeautifulSoup:
        soup = await self.fetch_and_parse(url)
        if "Too Many Requests" in soup.text:
            soup = await self.fetch_and_parse(url, proxy=ConfigManager().get("korone", "PROXY"))

        return soup

    @staticmethod
    def extract_specs(specs_tables: list) -> dict[str, str]:
        info = {}
        out = {}
        for table in specs_tables:
            details = {}
            header = ""
            detail = ""
            feature = ""
            for tr in table.findAll("tr"):
                for th in tr.findAll("th"):
                    feature = th.text.strip()
                for td in tr.findAll("td", {"class": "ttl"}):
                    header = td.text.strip()
                    if header == "\u00a0":
                        header = "info"
                for td in tr.findAll("td", {"class": "nfo"}):
                    detail = td.text.strip()
                details[header] = detail
            out[feature] = details

        info["specs"] = out

        return info

    async def search(self, phone: str) -> list[PhoneSearchResult]:
        phone_html_encoded = urllib.parse.quote_plus(phone)
        search_url = (
            f"https://m.gsmarena.com/results.php3?sQuickSearch=yes&sName={phone_html_encoded}"
        )
        soup = await self.fetch_with_retry(search_url)
        found_phones = soup.select("div.general-menu.material-card ul li")

        return [
            PhoneSearchResult(
                name=phone_tag.find("img").get("title"),  # type: ignore
                url=f"{phone_tag.find('a').get('href')}",  # type: ignore
            )
            for phone_tag in found_phones
        ]

    async def check_phone_details(self, url: str):
        url = f"https://www.gsmarena.com/{url}"
        soup = await GSMArena().fetch_with_retry(url)
        specs_tables = soup.findAll("table", {"cellspacing": "0"})

        phone_specs_temp = self.extract_specs(specs_tables)

        meta = list(soup.findAll("script", {"language": "javascript"})[0].text.splitlines())
        name = next(i for i in meta if "ITEM_NAME" in i).split('"')[1]
        picture = next(i for i in meta if "ITEM_IMAGE" in i).split('"')[1]

        phone_specs_temp["name"] = name
        phone_specs_temp["picture"] = picture
        phone_specs_temp["url"] = url

        return phone_specs_temp

    @staticmethod
    def build_keyboard(search_result: list[PhoneSearchResult]) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        for phone in search_result:
            keyboard.row(
                InlineKeyboardButton(
                    text=phone.name, callback_data=GetDeviceCallback(device=phone.url).pack()
                )
            )

        return keyboard.as_markup()  # type: ignore

    @Korone.on_message(filters.command(CMDS))
    async def handle(self, client: Client, message: Message) -> None:
        if message.command is None:
            await message.reply_text(_("Please enter a phone name to search."))
            return

        query: str = get_command_arg(message)
        devices = await self.search(query)

        if not devices:
            await message.reply_text(_("No devices found."))
            return

        if len(devices) == 1:
            phone = await self.check_phone_details(devices[0].url)
            await message.reply_text(text=format_phone(phone))
            return

        keyboard = create_pagination_layout(devices, query, 1)
        await message.reply_text(
            _("Search results for: <b>{device}</b>").format(device=query),
            reply_markup=keyboard.as_markup(),
        )


class ListGSMArena(CallbackQueryHandler):
    @Korone.on_callback_query(DevicePageCallback.filter())
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        if not callback.data:
            return

        query: str = DevicePageCallback.unpack(callback.data).device
        page: int = DevicePageCallback.unpack(callback.data).page

        devices = await GSMArena().search(query)
        keyboard = create_pagination_layout(devices, query, page)
        with suppress(MessageNotModified):
            await callback.edit_message_reply_markup(keyboard.as_markup())  # type: ignore


class GetGSMArena(CallbackQueryHandler):
    @Korone.on_callback_query(GetDeviceCallback.filter())
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        if not callback.data:
            return

        query: str = GetDeviceCallback.unpack(callback.data).device
        phone = await GSMArena().check_phone_details(query)

        with suppress(MessageNotModified):
            await callback.edit_message_text(text=format_phone(phone))
