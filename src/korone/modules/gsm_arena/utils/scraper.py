# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import urllib.parse
from datetime import timedelta

import httpx
from lxml import html
from lxml.html import HtmlElement

from korone.config import ConfigManager
from korone.utils.caching import cache
from korone.utils.i18n import gettext as _
from korone.utils.logging import get_logger

from .types import Phone, PhoneSearchResult

logger = get_logger(__name__)

CORS: str = ConfigManager.get("korone", "CORS_BYPASS")

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


def format_phone(phone: Phone) -> str:
    attributes_dict = {
        _("Status"): phone.status,
        _("Network"): phone.network,
        _("Weight"): phone.weight,
        _("Display"): phone.display,
        _("Chipset"): phone.chipset,
        _("Memory"): phone.memory,
        _("Rear Camera"): phone.main_camera,
        _("Front Camera"): phone.selfie_camera,
        _("3.5mm jack"): phone.jack,
        _("USB"): phone.usb,
        _("Sensors"): phone.sensors,
        _("Battery"): phone.battery,
        _("Charging"): phone.charging,
    }

    attributes = [
        f"<b>{key}:</b> {value}"
        for key, value in attributes_dict.items()
        if value and value.strip() and value.strip() != "-"
    ]

    return f"<a href='{phone.url}'>{phone.name}</a>\n\n{'\n\n'.join(attributes)}"


@cache(ttl=timedelta(days=1))
async def fetch_html(url: str) -> str:
    try:
        async with httpx.AsyncClient(headers=HEADERS, http2=True) as session:
            response = await session.get(f"{CORS}/{url}")
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        await logger.aerror("[GSM Arena] HTTP error occurred: %s", e)
        raise
    except httpx.RequestError as e:
        await logger.aerror("[GSM Arena] Request error occurred: %s", e)
        raise


def extract_specs_from_tables(specs_tables: list[HtmlElement]) -> dict[str, dict[str, str]]:
    specs = {}

    for table in specs_tables:
        category_elements = table.xpath(".//th")
        if not category_elements:
            continue

        category = category_elements[0].text_content().strip()
        specs[category] = {}

        for tr in table.xpath(".//tr"):
            header_elements = tr.xpath(".//td[@class='ttl']")
            value_elements = tr.xpath(".//td[@class='nfo']")

            if not header_elements or not value_elements:
                continue

            header = header_elements[0].text_content().strip()
            value = value_elements[0].text_content().strip()

            if header == "\u00a0":
                header = "info"

            specs[category][header] = value

    return specs


async def search_phone(query: str) -> list[PhoneSearchResult]:
    try:
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://m.gsmarena.com/results.php3?sQuickSearch=yes&sName={encoded_query}"

        html_content = await fetch_html(search_url)
        tree = html.fromstring(html_content)
        found_phones = tree.xpath("//div[@class='general-menu material-card']//ul//li")

        results = []
        for phone_tag in found_phones:
            try:
                name = phone_tag.xpath(".//img/@title")[0]
                url = phone_tag.xpath(".//a/@href")[0]
                results.append(PhoneSearchResult(name=name, url=url))
            except IndexError:
                continue

        return results
    except Exception as e:
        await logger.aerror("[GSM Arena] Error searching for phone: %s", e)
        return []


async def check_phone_details(url: str) -> Phone | None:
    try:
        complete_url = f"https://www.gsmarena.com/{url}"
        html_content = await fetch_html(complete_url)
        tree = html.fromstring(html_content)

        specs_tables = tree.xpath("//table[@cellspacing='0']")
        specs = extract_specs_from_tables(specs_tables)

        meta_scripts = tree.xpath("//script[@language='javascript']")
        if not meta_scripts:
            await logger.aerror("[GSM Arena] No metadata scripts found on the page")
            return None

        meta_content = meta_scripts[0].text_content().splitlines()
        name = extract_meta_data(meta_content, "ITEM_NAME")
        picture = extract_meta_data(meta_content, "ITEM_IMAGE")

        return Phone(name=name, url=complete_url, picture=picture, specs=specs)

    except Exception as e:
        await logger.aerror("[GSM Arena] Error checking phone details: %s", e)
        return None


def extract_meta_data(meta_lines: list[str], key: str) -> str:
    try:
        for line in meta_lines:
            if key in line:
                parts = line.split('"')
                if len(parts) >= 2:
                    return parts[1]
        return ""
    except Exception:
        logger.warning("[GSM Arena] Metadata key '%s' not found or invalid format.", key)
        return ""
