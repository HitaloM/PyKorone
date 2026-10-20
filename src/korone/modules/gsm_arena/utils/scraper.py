import re
import unicodedata
import urllib.parse
from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import aiohttp
from lxml import html
from lxml.etree import ParserError
from pydantic import TypeAdapter, ValidationError

from korone.config import CONFIG
from korone.http import RetryPolicy, http_client
from korone.utils.cached import Cached

from .errors import GSMArenaAccessError, GSMArenaParseError, GSMArenaRequestError, GSMArenaUnavailableError
from .types import Phone, PhoneSearchResult, Specs

if TYPE_CHECKING:
    from lxml.html import HtmlElement

BASE_URL = "https://www.gsmarena.com"
CACHE_TTL = 60 * 60 * 24
RETRY_POLICY: Final[RetryPolicy] = RetryPolicy(
    attempts=2,
    timeout=aiohttp.ClientTimeout(total=15, connect=5, sock_read=10),
    retryable_statuses=frozenset({502, 503, 504}),
    backoff_seconds=(1.0,),
    retry_timeouts=False,
    retry_client_errors=False,
    respect_retry_after=True,
    max_retry_after_seconds=5,
    buffer_response_statuses=frozenset({200}),
)

HEADERS = {
    "accept": "text/html, application/json;q=0.9, */*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": "PyKorone GSMArena integration",
}
_DEVICE_PATH = re.compile(r"/[a-zA-Z0-9_()+,\[\]'&-]+-\d+\.php")
_CATALOG_PATH = re.compile(r"AUTOCOMPLETE_LIST_URL\s*=\s*[\"'](/quicksearch-\d+\.jpg)[\"']")
# The site's autocomplete.js defines maker, ID, URL name, search aliases,
# thumbnail, and an optional display-name override in each catalog row.
type _CatalogRow = tuple[int, int, str, str, str] | tuple[int, int, str, str, str, str]
_CATALOG_ADAPTER = TypeAdapter(tuple[dict[str, str], list[_CatalogRow]])


@dataclass(frozen=True, slots=True, kw_only=True)
class _CatalogDevice:
    result: PhoneSearchResult
    names: tuple[str, ...]
    aliases: str


def _build_request_url(url: str) -> str:
    if CONFIG.cors_bypass_url is None:
        return url
    return f"{str(CONFIG.cors_bypass_url).rstrip('/')}/{url}"


def _device_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(urllib.parse.urljoin(f"{BASE_URL}/", url))
    if (
        parsed.scheme != "https"
        or parsed.netloc not in {"www.gsmarena.com", "m.gsmarena.com"}
        or not _DEVICE_PATH.fullmatch(parsed.path)
        or parsed.query
        or parsed.fragment
    ):
        msg = "GSMArena returned an invalid device link"
        raise GSMArenaParseError(msg)
    return f"{BASE_URL}{parsed.path}"


def normalize_query(query: str) -> str:
    value = unicodedata.normalize("NFKC", query).casefold().replace("+", " plus ")
    return " ".join(re.sub(r"[\W_]+", " ", value).split())


def _parse_document(content: str) -> HtmlElement:
    try:
        tree = html.fromstring(content)
    except (ParserError, ValueError) as error:
        msg = "GSMArena returned invalid HTML"
        raise GSMArenaParseError(msg) from error

    title = " ".join(tree.xpath("//title/text()")).casefold()
    if (
        "turnstile" in title
        or "just a moment" in title
        or "access denied" in title
        or tree.xpath(
            "//form[contains(@action, 'turnstile-verify')]"
            " | //div[contains(concat(' ', normalize-space(@class), ' '), ' cf-turnstile ')]"
            " | //*[@id='challenge-form' or @id='cf-challenge-running']"
            " | //script[contains(@src, '/cdn-cgi/challenge-platform/')]"
        )
    ):
        msg = "GSMArena requires human verification or has restricted access"
        raise GSMArenaAccessError(msg)
    if "service unavailable" in title or "temporarily unavailable" in title:
        raise GSMArenaUnavailableError
    return tree


def _element_text(element: HtmlElement) -> str:
    element = deepcopy(element)
    for line_break in element.xpath(".//br"):
        line_break.tail = "\n" + (line_break.tail or "")
    return "\n".join(part for line in element.text_content().splitlines() if (part := " ".join(line.split())))


def catalog_url_from_page(content: str) -> str:
    tree = _parse_document(content)
    for script in tree.xpath("//script[not(@src)]/text()"):
        if match := _CATALOG_PATH.search(script):
            return f"{BASE_URL}{match[1]}"
    msg = "GSMArena autocomplete catalog URL is missing"
    raise GSMArenaParseError(msg)


def parse_catalog(content: str) -> list[_CatalogDevice]:
    try:
        makers, rows = _CATALOG_ADAPTER.validate_json(content, strict=True)
    except ValidationError as error:
        # The catalog can also be replaced by an HTTP-200 challenge page.
        _parse_document(content)
        msg = "GSMArena returned an invalid autocomplete catalog"
        raise GSMArenaParseError(msg) from error
    if not makers or not rows:
        msg = "GSMArena returned an empty autocomplete catalog"
        raise GSMArenaParseError(msg)

    devices: list[_CatalogDevice] = []
    seen: set[int] = set()
    for row in rows:
        maker_id, phone_id, model, aliases, _thumbnail = row[:5]
        maker = makers.get(str(maker_id))
        if maker is None or phone_id <= 0 or not model.strip():
            msg = "GSMArena autocomplete entry is missing its manufacturer, ID or model"
            raise GSMArenaParseError(msg)
        url_name = f"{maker} {model}"
        display_model = row[5] if len(row) == 6 and row[5] else model
        # The catalog has an explicit empty maker for unbranded devices.
        name = f"{maker} {display_model}".strip()
        # Match _makePhoneURL in the site's autocomplete, including punctuation
        # such as '+' and parentheses used by real device pages.
        slug = re.sub(r"\s+|-|/|\.", "_", url_name.lower())
        url = _device_url(f"{slug}-{phone_id}.php")
        if phone_id not in seen:
            devices.append(
                _CatalogDevice(
                    result=PhoneSearchResult(name=name, url=url),
                    names=tuple(normalize_query(value) for value in (name, url_name, display_model, model)),
                    aliases=normalize_query(f"{maker} {aliases}"),
                )
            )
            seen.add(phone_id)
    return devices


def match_catalog(devices: list[_CatalogDevice], query: str) -> list[PhoneSearchResult]:
    normalized = normalize_query(query)
    if not normalized:
        return []
    terms = [re.compile(r"\b" + re.escape(term)) for term in normalized.split()]
    alias_terms = [re.compile(r"\b" + re.escape(term) + r"\b") for term in normalized.split()]
    compact = normalized.replace(" ", "")
    exact: list[PhoneSearchResult] = []
    partial: list[PhoneSearchResult] = []
    for device in devices:
        if any(compact == name.replace(" ", "") for name in device.names):
            exact.append(device.result)
        elif (
            any(all(term.search(name) for term in terms) for name in device.names)
            or any(compact in name.replace(" ", "") for name in device.names)
            or all(term.search(device.aliases) for term in alias_terms)
        ):
            partial.append(device.result)
    # Preserve the catalog's relevance order after exact matches. Unlike the
    # browser dropdown, return every match for the bot's existing pagination.
    return exact + partial


def extract_specs_from_tables(specs_tables: list[HtmlElement]) -> Specs:
    specs: Specs = {}
    for table in specs_tables:
        categories = table.xpath(".//th")
        if not categories:
            continue
        category = _element_text(categories[0])
        attributes = specs.setdefault(category, {})
        for tr in table.xpath(".//tr"):
            headers = tr.find_class("ttl")
            values = tr.find_class("nfo")
            if not headers and not values:
                continue
            if not headers or not values:
                msg = "GSMArena specification row is incomplete"
                raise GSMArenaParseError(msg)
            header = _element_text(headers[0]) or "info"
            value = _element_text(values[0])
            if not value:
                msg = "GSMArena specification value is missing"
                raise GSMArenaParseError(msg)
            attributes[header] = "\n".join(filter(None, (attributes.get(header, ""), value)))
        if not category or not attributes:
            msg = "GSMArena specification table is incomplete"
            raise GSMArenaParseError(msg)
    return specs


def parse_phone_details(content: str, url: str) -> Phone:
    tree = _parse_document(content)
    names = tree.xpath("//h1[@data-spec='modelname']") or tree.find_class("specs-phone-name-title")
    specs = extract_specs_from_tables(tree.xpath("//*[@id='specs-list']//table"))
    if not names or not (name := _element_text(names[0])) or not specs:
        msg = "GSMArena device name or specifications are missing"
        raise GSMArenaParseError(msg)
    pictures = tree.xpath("//*[contains(concat(' ', normalize-space(@class), ' '), ' specs-photo-main ')]//img/@src")
    picture = urllib.parse.urljoin(url, pictures[0]) if pictures else ""
    return Phone(name=name, url=url, picture=picture, specs=specs)


async def _fetch_text(url: str) -> str:
    request_url = _build_request_url(url)
    try:
        async with http_client.session.get(
            request_url, headers=HEADERS, timeout=RETRY_POLICY.request_timeout, middlewares=(RETRY_POLICY,)
        ) as response:
            response.raise_for_status()
            content = await response.text()
    except aiohttp.ClientResponseError as error:
        if error.status in {401, 403, 429}:
            raise GSMArenaAccessError(status_code=error.status, target_url=url) from error
        if error.status >= 500:
            raise GSMArenaUnavailableError(status_code=error.status, target_url=url) from error
        raise GSMArenaRequestError(status_code=error.status, target_url=url) from error
    except (TimeoutError, aiohttp.ClientError) as error:
        raise GSMArenaRequestError(target_url=url) from error
    except UnicodeError as error:
        msg = "GSMArena returned unreadable content"
        raise GSMArenaParseError(msg) from error

    return content


# Only validated pages enter this versioned cache. The old cache may contain
# HTTP-200 challenge pages; its keys must never be reused after this change.
@Cached(ttl=CACHE_TTL, key="gsmarena:html:v2", early_recompute_beta=0)
async def fetch_html(url: str) -> str:
    content = await _fetch_text(url)
    parse_phone_details(content, url)
    return content


@Cached(ttl=CACHE_TTL, key="gsmarena:catalog:v1", early_recompute_beta=0)
async def fetch_catalog() -> str:
    # Discover the current version instead of pinning a stale catalog filename.
    catalog_url = catalog_url_from_page(await _fetch_text(f"{BASE_URL}/"))
    content = await _fetch_text(catalog_url)
    parse_catalog(content)
    return content


async def search_phone(query: str) -> list[PhoneSearchResult]:
    if not normalize_query(query):
        return []
    return match_catalog(parse_catalog(await fetch_catalog()), query)


async def check_phone_details(url: str) -> Phone:
    complete_url = _device_url(url)
    return parse_phone_details(await fetch_html(complete_url), complete_url)
