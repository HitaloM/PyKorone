import urllib.parse
from typing import TYPE_CHECKING

import aiohttp
from lxml import html
from stfu_tg import Doc, KeyValue, Url

from korone.config import CONFIG
from korone.logger import get_logger
from korone.utils.aiohttp_session import HTTPClient
from korone.utils.cached import Cached
from korone.utils.i18n import gettext as _

from .types import Phone, PhoneSearchResult

if TYPE_CHECKING:
    from lxml.html import HtmlElement

logger = get_logger(__name__)

BASE_URL = "https://www.gsmarena.com"
MOBILE_BASE_URL = "https://m.gsmarena.com"
CACHE_TTL = 60 * 60 * 24

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


@Cached(ttl=CACHE_TTL, key="gsmarena:html")
async def fetch_html(url: str) -> str:
    try:
        proxy_url = f"{CONFIG.cors_bypass_url.rstrip('/')}/{url}"
        timeout = aiohttp.ClientTimeout(total=20)
        session = await HTTPClient.get_session()
        async with session.get(proxy_url, headers=HEADERS, timeout=timeout) as response:
            response.raise_for_status()
            return await response.text()
    except aiohttp.ClientResponseError as err:
        await logger.aerror("[GSM Arena] HTTP error occurred", error=str(err))
        raise
    except aiohttp.ClientError as err:
        await logger.aerror("[GSM Arena] Request error occurred", error=str(err))
        raise


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

    doc = Doc(Url(phone.name, phone.url))

    for key, value in attributes_dict.items():
        if value and value.strip() and value.strip() != "-":
            doc += KeyValue(key, value)

    return str(doc)


def extract_specs_from_tables(specs_tables: list[HtmlElement]) -> dict[str, dict[str, str]]:
    specs: dict[str, dict[str, str]] = {}

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
            header = "info" if header == "\u00a0" else header

            specs[category][header] = value

    return specs


async def search_phone(query: str) -> list[PhoneSearchResult]:
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"{MOBILE_BASE_URL}/results.php3?sQuickSearch=yes&sName={encoded_query}"

    html_content = await fetch_html(search_url)
    tree = html.fromstring(html_content)
    found_phones = tree.xpath("//div[@class='general-menu material-card']//ul//li")

    results: list[PhoneSearchResult] = []
    for phone_tag in found_phones:
        names = phone_tag.xpath(".//img/@title")
        urls = phone_tag.xpath(".//a/@href")
        if not names or not urls:
            continue
        results.append(PhoneSearchResult(name=names[0], url=urls[0]))

    return results


async def check_phone_details(url: str) -> Phone | None:
    complete_url = url if url.startswith("http") else f"{BASE_URL}/{url.lstrip('/')}"
    html_content = await fetch_html(complete_url)
    tree = html.fromstring(html_content)

    specs = extract_specs_from_tables(tree.xpath("//table[@cellspacing='0']"))

    meta_scripts = tree.xpath("//script[@language='javascript']")
    if not meta_scripts:
        await logger.aerror("[GSM Arena] No metadata scripts found on the page")
        return None

    meta_content = meta_scripts[0].text_content().splitlines()
    return Phone(
        name=extract_meta_data(meta_content, "ITEM_NAME"),
        url=complete_url,
        picture=extract_meta_data(meta_content, "ITEM_IMAGE"),
        specs=specs,
    )


def extract_meta_data(meta_lines: list[str], key: str) -> str:
    for line in meta_lines:
        if key not in line:
            continue
        parts = line.split('"')
        if len(parts) >= 2:
            return parts[1]
    logger.warning("[GSM Arena] Metadata key '%s' not found or invalid format.", key)
    return ""
