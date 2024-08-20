# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import urllib.parse
from datetime import timedelta

import httpx
from lxml import html

from korone import cache
from korone.utils.i18n import gettext as _

from .types import PhoneSearchResult

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
    "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Referer": "https://m.gsmarena.com/",
    "Accept-Charset": "utf-8",
}


def get_data_from_specs(specs_data: dict, category: str, attributes: list) -> str:
    details = specs_data.get("specs", {}).get(category, {})
    return "\n".join(details.get(attr, "") for attr in attributes)


def get_camera_data(specs_data: dict, category: str) -> str | None:
    details = specs_data.get("specs", {}).get(category, {})
    camera = next(iter(details.items()), (None, None))
    return f"{camera[0]} {camera[1]}" if all(camera) else None


def parse_specs(specs_data: dict) -> dict:
    categories = {
        "status": ("Launch", ["Status"]),
        "network": ("Network", ["Technology"]),
        "weight": ("Body", ["Weight"]),
        "jack": ("Sound", ["3.5mm jack"]),
        "usb": ("Comms", ["USB"]),
        "sensors": ("Features", ["Sensors"]),
        "battery": ("Battery", ["Type"]),
        "charging": ("Battery", ["Charging"]),
        "display": ("Display", ["Type", "Size", "Resolution"]),
        "chipset": ("Platform", ["Chipset", "CPU", "GPU"]),
        "main_camera": ("Main Camera", []),
        "selfie_camera": ("Selfie camera", []),
        "memory": ("Memory", ["Internal"]),
    }

    data = {
        key: get_data_from_specs(specs_data, cat, attrs)
        for key, (cat, attrs) in categories.items()
    }
    data["main_camera"] = get_camera_data(specs_data, "Main Camera") or ""
    data["selfie_camera"] = get_camera_data(specs_data, "Selfie camera") or ""
    data["name"] = specs_data.get("name", "")
    data["url"] = specs_data.get("url", "")

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
        if phone.get(value) and phone[value].strip() and phone[value].strip() != "-"
    ]

    return f"<a href='{phone["url"]}'>{phone["name"]}</a>\n\n{"\n\n".join(attributes)}"


@cache(ttl=timedelta(days=1))
async def fetch_html(url: str) -> str:
    async with httpx.AsyncClient(headers=HEADERS, http2=True) as session:
        response = await session.get(url)
        response.raise_for_status()
        encoding = response.encoding or "utf-8"
        return response.content.decode(encoding)


def extract_specs(specs_tables: list) -> dict:
    return {
        "specs": {
            feature: {
                (header if header != "\u00a0" else "info"): detail
                for tr in table.xpath(".//tr")
                for header in [td.text_content().strip() for td in tr.xpath(".//td[@class='ttl']")]
                for detail in [td.text_content().strip() for td in tr.xpath(".//td[@class='nfo']")]
            }
            for table in specs_tables
            for feature in [th.text_content().strip() for th in table.xpath(".//th")]
        }
    }


async def search_phone(phone: str) -> list[PhoneSearchResult]:
    phone_html_encoded = urllib.parse.quote_plus(phone)
    search_url = f"https://m.gsmarena.com/results.php3?sQuickSearch=yes&sName={phone_html_encoded}"
    html_content = await fetch_html(search_url)
    tree = html.fromstring(html_content)
    found_phones = tree.xpath("//div[@class='general-menu material-card']//ul//li")

    return [
        PhoneSearchResult(
            name=phone_tag.xpath(".//img/@title")[0],
            url=phone_tag.xpath(".//a/@href")[0],
        )
        for phone_tag in found_phones
    ]


async def check_phone_details(url: str) -> dict[str, str]:
    url = f"https://www.gsmarena.com/{url}"
    html_content = await fetch_html(url)
    tree = html.fromstring(html_content)
    specs_tables = tree.xpath("//table[@cellspacing='0']")

    phone_specs_temp = extract_specs(specs_tables)

    meta_scripts = tree.xpath("//script[@language='javascript']")
    if not meta_scripts:
        msg = "No metadata scripts found on the page"
        raise ValueError(msg)

    meta = meta_scripts[0].text_content().splitlines()
    name = extract_meta_data(meta, "ITEM_NAME")
    picture = extract_meta_data(meta, "ITEM_IMAGE")

    phone_specs_temp.update({"name": name, "picture": picture, "url": url})

    return phone_specs_temp


def extract_meta_data(meta: list[str], key: str) -> str:
    return next((line.split('"')[1] for line in meta if key in line), "")
