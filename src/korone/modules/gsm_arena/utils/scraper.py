# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import urllib.parse
from datetime import timedelta
from typing import Any

import httpx
from lxml import html

from korone.utils.caching import cache
from korone.utils.i18n import gettext as _
from korone.utils.logging import logger

from .types import PhoneSearchResult

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
    "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0",
    "referer": "https://m.gsmarena.com/",
}


def get_data_from_specs(specs_data: dict[str, Any], category: str, attributes: list[str]) -> str:
    details = specs_data.get("specs", {}).get(category, {})
    return "\n".join(details.get(attr, "") for attr in attributes)


def get_camera_data(specs_data: dict[str, Any], category: str) -> str | None:
    details = specs_data.get("specs", {}).get(category, {})
    camera = next(iter(details.items()), (None, None))
    return f"{camera[0]} {camera[1]}" if all(camera) else None


def parse_specs(specs_data: dict[str, Any]) -> dict[str, str]:
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


def format_phone(phone: dict[str, Any]) -> str:
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
    try:
        async with httpx.AsyncClient(headers=HEADERS, http2=True) as session:
            response = await session.get(f"https://cors-bypass.amano.workers.dev/{url}")
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        await logger.aerror("[GSM Arena] HTTP error occurred: %s", e)
        raise
    except httpx.RequestError as e:
        await logger.aerror("[GSM Arena] Request error occurred: %s", e)
        raise


def extract_specs(specs_tables: list[Any]) -> dict[str, Any]:
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
    try:
        phone_html_encoded = urllib.parse.quote_plus(phone)
        search_url = (
            f"https://m.gsmarena.com/results.php3?sQuickSearch=yes&sName={phone_html_encoded}"
        )
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
    except Exception as e:
        await logger.aerror("[GSM Arena] Error searching for phone: %s", e)
        return []


async def check_phone_details(url: str) -> dict[str, str]:
    try:
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
    except Exception as e:
        await logger.aerror("[GSM Arena] Error checking phone details: %s", e)
        return {}


def extract_meta_data(meta: list[str], key: str) -> str:
    try:
        return next((line.split('"')[1] for line in meta if key in line), "")
    except StopIteration:
        logger.warning("[GSM Arena] Metadata key '%s' not found.", key)
        return ""
