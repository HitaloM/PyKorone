from __future__ import annotations

import asyncio
import contextlib
import ipaddress
import re
from typing import Any

from .misc import _extract_hostname

WHOIS_PORT = 43
TIMEOUT = 10

REFERRAL_PATTERNS = [
    re.compile(r"refer:\s*(?P<server>[^\s]+)", re.IGNORECASE),
    re.compile(r"Whois Server:\s*(?P<server>[^\s]+)", re.IGNORECASE),
    re.compile(r"Registrar WHOIS Server:\s*(?P<server>[^\s]+)", re.IGNORECASE),
    re.compile(r"whois:\s*(?P<server>[^\s]+)", re.IGNORECASE),
    re.compile(r"ReferralServer:\s*(?P<server>[^\s]+)", re.IGNORECASE),
]

FIELDS_MAP = {
    "domain_name": re.compile(r"^\s*(?:Domain Name|domain):\s*(?P<val>.+)", re.IGNORECASE | re.MULTILINE),
    "registrar": re.compile(r"^\s*(?:Registrar|Sponsoring Registrar):\s*(?P<val>.+)", re.IGNORECASE | re.MULTILINE),
    "created": re.compile(
        r"^\s*(?:Creation Date|Created|Registration Date):\s*(?P<val>.+)", re.IGNORECASE | re.MULTILINE
    ),
    "updated": re.compile(
        r"^\s*(?:Updated Date|Last Updated|Domain Last Updated Date):\s*(?P<val>.+)", re.IGNORECASE | re.MULTILINE
    ),
    "expires": re.compile(
        r"^\s*(?:Registry Expiry Date|Expiration Date|Expires|o expire):\s*(?P<val>.+)", re.IGNORECASE | re.MULTILINE
    ),
    "name_servers": re.compile(r"^\s*(?:Name Server|nserver):\s*(?P<val>.+)", re.IGNORECASE | re.MULTILINE),
}


async def _send_whois_query(server: str, query: str) -> str:
    server = server.replace("http://", "").replace("https://", "").replace("whois://", "").split("/")[0]
    server = server.split("]")[0] + "]" if server.startswith("[") and "]" in server else server.split(":")[0]

    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(server, WHOIS_PORT), timeout=TIMEOUT)
    except TimeoutError, OSError:
        return ""

    try:
        writer.write(f"{query}\r\n".encode())
        await writer.drain()

        response_bytes = b""
        while True:
            try:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=TIMEOUT)
                if not chunk:
                    break
                response_bytes += chunk
            except TimeoutError:
                break

        try:
            return response_bytes.decode("utf-8", errors="ignore")
        except UnicodeDecodeError:
            return response_bytes.decode("latin-1", errors="ignore")

    finally:
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()


def _parse_raw_text(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}

    for key, pattern in FIELDS_MAP.items():
        matches = pattern.findall(text)
        if matches:
            cleaned = []
            seen = set()
            for m in matches:
                val = m.strip()
                if val and val.lower() not in seen:
                    cleaned.append(val)
                    seen.add(val.lower())

            if key == "name_servers":
                data[key] = cleaned
            else:
                data[key] = cleaned if len(cleaned) > 1 else cleaned[0]

    return data


async def _recursive_lookup(domain: str) -> tuple[str, dict[str, Any]]:
    tld = domain.rsplit(".", maxsplit=1)[-1]
    current_server = "whois.iana.org"

    seen_servers = {current_server}
    final_text = ""

    for _ in range(5):
        query_str = domain if current_server != "whois.iana.org" else tld

        response_text = await _send_whois_query(current_server, query_str)
        if not response_text:
            break

        final_text = response_text

        next_server = None
        for pattern in REFERRAL_PATTERNS:
            if match := pattern.search(response_text):
                candidate = match.group("server").strip().lower()
                if candidate and candidate not in seen_servers:
                    next_server = candidate
                    break

        if next_server:
            seen_servers.add(next_server)
            current_server = next_server
        else:
            break

    parsed = _parse_raw_text(final_text)
    return final_text, parsed


async def query_whois(domain: str) -> dict[str, Any] | None:
    if not domain:
        return None

    try:
        _, parsed_dict = await _recursive_lookup(domain)
        if not parsed_dict:
            return None
    except TimeoutError, OSError:
        return None
    else:
        return parsed_dict


def parse_whois_response(data: dict[str, Any]) -> dict[str, str] | None:
    if not data:
        return None

    info: dict[str, str] = {}

    def get_first(val: str | list[str] | None) -> str:
        if isinstance(val, list) and val:
            return str(val[0])
        return str(val) if val else ""

    def clean_date(val: str | list[str] | None) -> str:
        raw = get_first(val)
        return raw.split(" ")[0].split("T")[0]

    if domain_name := data.get("domain_name"):
        info["Domain Name"] = get_first(domain_name).lower()

    if registrar := data.get("registrar"):
        info["Registrar"] = get_first(registrar)

    if created := data.get("created"):
        info["Creation Date"] = clean_date(created)

    if updated := data.get("updated"):
        info["Updated Date"] = clean_date(updated)

    if expires := data.get("expires"):
        info["Expiration Date"] = clean_date(expires)

    if name_servers := data.get("name_servers"):
        if isinstance(name_servers, list):
            ns_list = [str(ns).lower().rstrip(".") for ns in name_servers if ns]
            if ns_list:
                info["Name Servers"] = ", ".join(ns_list)
        elif isinstance(name_servers, str):
            info["Name Servers"] = name_servers.lower().rstrip(".")

    return info or None


def normalize_domain(value: str) -> str | None:
    if not value:
        return None

    host = _extract_hostname(value)
    if not host:
        return None

    try:
        ipaddress.ip_address(host)
    except ValueError:
        return host
    else:
        return None
