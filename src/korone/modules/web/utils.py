from __future__ import annotations

import ipaddress
import re
import socket
from subprocess import PIPE
from typing import Any
from urllib.parse import urlparse

import aiohttp
from anyio import create_task_group, run_process
from anyio.to_thread import run_sync

IPINFO_URL = "https://ipinfo.io/{target}/json"
CF_DNS_URL = "https://cloudflare-dns.com/dns-query"


async def run_whois(domain: str) -> str:
    result = await run_process(["whois", domain], stdout=PIPE, stderr=PIPE)
    stdout = (result.stdout or b"").decode()
    stderr = (result.stderr or b"").decode()
    return stdout if result.returncode == 0 else stderr


def parse_whois_output(output: str) -> dict[str, str] | None:
    info: dict[str, str] = {}

    if domain_name := re.search(r"Domain Name:\s*(.*)", output, re.IGNORECASE):
        info["Domain Name"] = domain_name[1].strip()

    if registrar := re.search(r"Registrar:\s*(.*)", output, re.IGNORECASE):
        info["Registrar"] = registrar[1].strip()

    if creation_date := re.search(r"Creation Date:\s*(.*)", output, re.IGNORECASE):
        info["Creation Date"] = creation_date[1].strip()

    if updated_date := re.search(r"Updated Date:\s*(.*)", output, re.IGNORECASE):
        info["Updated Date"] = updated_date[1].strip()

    expiration_date = re.search(r"Registry Expiry Date:\s*(.*)", output, re.IGNORECASE) or re.search(
        r"Expiration Date:\s*(.*)", output, re.IGNORECASE
    )
    if expiration_date:
        info["Expiration Date"] = expiration_date[1].strip()

    if name_servers := re.findall(r"Name Server:\s*(.*)", output, re.IGNORECASE):
        info["Name Servers"] = ", ".join([ns.strip() for ns in name_servers])

    return info or None


async def fetch_ip_info(ip_or_domain: str) -> dict[str, Any] | None:
    url = IPINFO_URL.format(target=ip_or_domain)
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                data.pop("readme", None)
                return data
        except aiohttp.ClientError:
            return None


async def fetch_dns_info(hostname: str, record_type: str) -> list[str]:
    params = {"name": hostname, "type": record_type}
    headers = {"accept": "application/dns-json"}
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(CF_DNS_URL, params=params, headers=headers) as response:
                if response.status != 200:
                    return []
                data = await response.json()
                answers = data.get("Answer", [])
                expected_type = 1 if record_type == "A" else 28
                return [answer["data"] for answer in answers if answer.get("type") == expected_type]
        except aiohttp.ClientError:
            return []


async def resolve_hostname(hostname: str) -> list[str]:
    answers: dict[str, list[str]] = {"A": [], "AAAA": []}

    async def fetch(record_type: str) -> None:
        answers[record_type] = await fetch_dns_info(hostname, record_type)

    async with create_task_group() as tg:
        for record_type in ("A", "AAAA"):
            tg.start_soon(fetch, record_type)

    resolved = answers["A"] + answers["AAAA"]
    if resolved:
        return resolved

    return await run_sync(_resolve_hostname_system, hostname)


def _resolve_hostname_system(hostname: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return []

    resolved: list[str] = []
    for info in infos:
        sockaddr = info[4]
        ip = sockaddr[0]
        if ip not in resolved:
            resolved.append(ip)
    return resolved


def _extract_hostname(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.hostname:
        return parsed.hostname
    if parsed.scheme:
        return None
    parsed = urlparse(f"http://{value}")
    return parsed.hostname


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

    return None
