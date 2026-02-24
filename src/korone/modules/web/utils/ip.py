from __future__ import annotations

import asyncio
import ipaddress
import socket
from typing import Any

import aiohttp
import orjson

from korone.utils.aiohttp_session import HTTPClient

from .misc import _extract_hostname

IPINFO_URL = "https://ipinfo.io/{target}/json"
CF_DNS_URL = "https://cloudflare-dns.com/dns-query"


async def fetch_ip_info(ip_or_domain: str) -> dict[str, Any] | None:
    url = IPINFO_URL.format(target=ip_or_domain)
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


async def fetch_dns_info(hostname: str, record_type: str) -> list[str]:
    params = {"name": hostname, "type": record_type}
    headers = {"accept": "application/dns-json"}
    timeout = aiohttp.ClientTimeout(total=10)

    session = await HTTPClient.get_session()
    try:
        async with session.get(CF_DNS_URL, timeout=timeout, params=params, headers=headers) as response:
            if response.status != 200:
                return []
            data = await response.json(loads=orjson.loads)
            answers = data.get("Answer", [])
            expected_type = 1 if record_type == "A" else 28
            return [answer["data"] for answer in answers if answer.get("type") == expected_type]
    except aiohttp.ClientError:
        return []


async def resolve_hostname(hostname: str) -> list[str]:
    answers: dict[str, list[str]] = {"A": [], "AAAA": []}

    async def fetch(record_type: str) -> None:
        answers[record_type] = await fetch_dns_info(hostname, record_type)

    async with asyncio.TaskGroup() as tg:
        for record_type in ("A", "AAAA"):
            tg.create_task(fetch(record_type))

    resolved = answers["A"] + answers["AAAA"]
    if resolved:
        return resolved

    return await asyncio.to_thread(_resolve_hostname_system, hostname)


def _resolve_hostname_system(hostname: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return []

    resolved: list[str] = []
    for info in infos:
        sockaddr = info[4]
        ip = str(sockaddr[0])
        if ip not in resolved:
            resolved.append(ip)
    return resolved


async def get_ips_from_string(value: str) -> list[str]:
    try:
        ip = ipaddress.ip_address(value)
        return [str(ip)]
    except ValueError:
        host = _extract_hostname(value)
        if not host:
            return []

        try:
            ip = ipaddress.ip_address(host)
            return [str(ip)]
        except ValueError:
            ips = await resolve_hostname(host)
            ipv4s = [ip for ip in ips if ipaddress.ip_address(ip).version == 4]
            ipv6s = [ip for ip in ips if ipaddress.ip_address(ip).version == 6]
            return ipv6s + ipv4s
