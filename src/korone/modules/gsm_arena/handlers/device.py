# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import urllib.parse
from dataclasses import dataclass
from datetime import timedelta

import httpx
from bs4 import BeautifulSoup
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from korone import cache
from korone.config import ConfigManager
from korone.decorators import on_callback_query, on_message
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.handlers.message_handler import MessageHandler
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


def format_phone(phone: dict) -> str:
    attributes_dict = {
        _("Body"): "body",
        _("Display"): "display",
        _("Platform"): "platform",
        _("Memory"): "memory",
        _("Main Camera"): "main_camera",
        _("Selfie Camera"): "selfie_camera",
        _("Sound"): "sound",
        _("Comms"): "comms",
        _("Features"): "features",
        _("Battery"): "battery",
    }

    attributes = [f"<b>{key}</b>:\n{phone[value]}\n" for key, value in attributes_dict.items()]

    return (
        f"<b>{phone['name']}</b>\n\n{'\n'.join(attributes)} <a href='{phone['url']}'>&#8203;</a>"
    )


def create_pagination_layout(devices: list, query: str, page: int) -> InlineKeyboardBuilder:
    layout = Pagination(
        devices,
        item_data=lambda i, _: f"getdevice:{i.url}",
        item_title=lambda i, _: i.name,
        page_data=lambda pg: f"devicepage:{query}:{pg}",
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
        soup = await GSMArena.fetch_and_parse(url)
        if "Too Many Requests" in soup.text:
            soup = await self.fetch_and_parse(url, proxy=ConfigManager().get("korone", "PROXY"))

        return soup

    @staticmethod
    def extract_specs(specs_tables: list) -> dict[str, str]:
        specs_dict = {
            "Body": "body",
            "Display": "display",
            "Platform": "platform",
            "Memory": "memory",
            "Main Camera": "main_camera",
            "Selfie camera": "selfie_camera",
            "Sound": "sound",
            "Comms": "comms",
            "Features": "features",
            "Battery": "battery",
        }

        phone_specs_temp = {}

        for table in specs_tables:
            row_title = table.select("th")[0].text
            specs = table.select("td")
            this_spec = ""

            for idx, spec in enumerate(specs):
                current_spec = spec.text.strip()
                if current_spec == "":
                    this_spec = this_spec.rstrip() + ", " + current_spec
                    continue

                this_spec += current_spec
                if idx % 2 == 0:
                    this_spec += ": "
                else:
                    this_spec += "\n"

            this_spec = this_spec.rstrip()

            if row_title in specs_dict:
                phone_specs_temp[specs_dict[row_title]] = this_spec

        return phone_specs_temp

    @staticmethod
    async def search(phone: str) -> list[PhoneSearchResult]:
        phone_html_encoded = urllib.parse.quote_plus(phone)
        search_url = (
            f"https://m.gsmarena.com/results.php3?sQuickSearch=yes&sName={phone_html_encoded}"
        )
        soup = await GSMArena().fetch_with_retry(search_url)
        found_phones = soup.select("div.general-menu.material-card ul li")

        return [
            PhoneSearchResult(
                name=phone_tag.find("img").get("title"),  # type: ignore
                url=f"{phone_tag.find('a').get('href')}",  # type: ignore
            )
            for phone_tag in found_phones
        ]

    @staticmethod
    async def check_phone_details(url: str):
        url = f"https://www.gsmarena.com/{url}"
        soup = await GSMArena().fetch_with_retry(url)
        specs_tables = soup.select("div#specs-list table")

        phone_specs_temp = GSMArena.extract_specs(specs_tables)

        name = soup.select("h1.specs-phone-name-title")[0].text

        phone_specs_temp["name"] = name
        phone_specs_temp["url"] = url

        return phone_specs_temp

    @staticmethod
    def build_keyboard(search_result: list[PhoneSearchResult]) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        for phone in search_result:
            keyboard.row(
                InlineKeyboardButton(text=phone.name, callback_data=f"device:{phone.url}")
            )

        return keyboard.as_markup()  # type: ignore

    @on_message(filters.command(CMDS))
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
    @on_callback_query(filters.regex(r"^devicepage:(.+):(\d+)$"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        if not callback.matches:
            return

        query: str = callback.matches[0].group(1)
        page: int = int(callback.matches[0].group(2))

        devices = await GSMArena.search(query)
        keyboard = create_pagination_layout(devices, query, page)
        await callback.edit_message_reply_markup(keyboard.as_markup())  # type: ignore


class GetGSMArena(CallbackQueryHandler):
    @on_callback_query(filters.regex(r"^getdevice:(.+)$"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        if not callback.matches:
            return

        query = callback.matches[0].group(1)
        phone = await GSMArena.check_phone_details(query)

        await callback.edit_message_text(text=format_phone(phone))
