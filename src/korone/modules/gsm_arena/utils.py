# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import urllib.parse
from dataclasses import dataclass
from datetime import timedelta

import httpx
from bs4 import BeautifulSoup
from hairydogm.keyboard import InlineKeyboardBuilder

from korone import cache
from korone.modules.gsm_arena.callback_data import DevicePageCallback, GetDeviceCallback
from korone.utils.i18n import gettext as _
from korone.utils.pagination import Pagination

HEADERS: dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
    "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Referer": "https://m.gsmarena.com/",
}


def create_pagination_layout(devices: list, query: str, page: int) -> InlineKeyboardBuilder:
    layout = Pagination(
        devices,
        item_data=lambda i, _: GetDeviceCallback(device=i.url).pack(),
        item_title=lambda i, _: i.name,
        page_data=lambda pg: DevicePageCallback(device=query, page=pg).pack(),
    )

    return layout.create(page, lines=8)


@dataclass(frozen=True, slots=True)
class PhoneSearchResult:
    name: str
    url: str


def get_data_from_specs(specs_data: dict, category: str, attribute: str) -> str:
    return specs_data.get("specs", {}).get(category, [{}]).get(attribute)


def get_data_from_specs_multiple_attributes(
    specs_data: dict, category: str, attributes: list
) -> str:
    details = specs_data.get("specs", {})
    return "\n".join(details.get(category, [{}]).get(attr, "") for attr in attributes)


def get_camera_data(specs_data: dict, category: str) -> str | None:
    details = specs_data.get("specs", {})
    camera = next(iter(details.get(category, [{}]).items()), (None, None))
    return f"{camera[0]} {camera[1]}" if all(camera) else None


def parse_specs(specs_data: dict) -> dict:
    data = {
        key: get_data_from_specs(specs_data, category, attribute)
        for category, attribute, key in [
            ("Launch", "Status", "status"),
            ("Network", "Technology", "network"),
            ("Body", "Weight", "weight"),
            ("Sound", "3.5mm jack", "jack"),
            ("Comms", "USB", "usb"),
            ("Features", "Sensors", "sensors"),
            ("Battery", "Type", "battery"),
            ("Battery", "Charging", "charging"),
        ]
    }

    for category, attributes, key in [
        ("Display", ["Type", "Size", "Resolution"], "display"),
        ("Platform", ["Chipset", "CPU", "GPU"], "chipset"),
    ]:
        data[key] = get_data_from_specs_multiple_attributes(specs_data, category, attributes)

    for category, key in [("Main Camera", "main_camera"), ("Selfie camera", "selfie_camera")]:
        camera_data = get_camera_data(specs_data, category)
        data[key] = camera_data or ""

    data["name"] = specs_data.get("name") or ""
    data["url"] = specs_data.get("url") or ""
    data["memory"] = get_data_from_specs(specs_data, "Memory", "Internal")

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

    return f"<a href='{phone["url"]}'>{phone["name"]}</a>\n\n{"\n\n".join(attributes)}"


@cache(ttl=timedelta(days=1))
async def fetch_and_parse(url: str) -> str:
    async with httpx.AsyncClient(headers=HEADERS, http2=True) as session:
        response = await session.get(
            f"https://cors-bypass.amano.workers.dev/{url}",
        )
        return response.text


def extract_specs(specs_tables: list) -> dict:
    return {
        "specs": {
            feature: {
                header if header != "\u00a0" else "info": detail
                for tr in table.findAll("tr")
                for header in [td.text.strip() for td in tr.findAll("td", {"class": "ttl"})]
                for detail in [td.text.strip() for td in tr.findAll("td", {"class": "nfo"})]
            }
            for table in specs_tables
            for feature in [th.text.strip() for th in table.findAll("th")]
        }
    }


async def search_phone(phone: str) -> list[PhoneSearchResult]:
    phone_html_encoded = urllib.parse.quote_plus(phone)
    search_url = f"https://m.gsmarena.com/results.php3?sQuickSearch=yes&sName={phone_html_encoded}"
    html = await fetch_and_parse(search_url)
    soup = BeautifulSoup(html, "lxml")
    found_phones = soup.select("div.general-menu.material-card ul li")

    return [
        PhoneSearchResult(
            name=phone_tag.find("img").get("title"),  # type: ignore
            url=f"{phone_tag.find("a").get("href")}",  # type: ignore
        )
        for phone_tag in found_phones
    ]


async def check_phone_details(url: str) -> dict[str, str]:
    url = f"https://www.gsmarena.com/{url}"
    html = await fetch_and_parse(url)
    soup = BeautifulSoup(html, "lxml")
    specs_tables = soup.findAll("table", {"cellspacing": "0"})

    phone_specs_temp = extract_specs(specs_tables)

    meta = list(soup.findAll("script", {"language": "javascript"})[0].text.splitlines())
    name = next(i for i in meta if "ITEM_NAME" in i).split('"')[1]
    picture = next(i for i in meta if "ITEM_IMAGE" in i).split('"')[1]

    phone_specs_temp.update({"name": name, "picture": picture, "url": url})

    return phone_specs_temp
