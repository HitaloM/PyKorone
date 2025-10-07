# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import ipaddress
import re
from subprocess import PIPE
from urllib.parse import urlparse

import httpx
from anyio import create_task_group, run_process


async def run_whois(domain: str) -> str:
    result = await run_process(["whois", domain], stdout=PIPE, stderr=PIPE)
    stdout = (result.stdout or b"").decode()
    stderr = (result.stderr or b"").decode()
    return stdout if result.returncode == 0 else stderr


def parse_whois_output(output: str) -> dict[str, str] | None:
    info = {}

    if domain_name := re.search(r"Domain Name:\s*(.*)", output, re.IGNORECASE):
        info["Domain Name"] = domain_name[1].strip()

    if registrar := re.search(r"Registrar:\s*(.*)", output, re.IGNORECASE):
        info["Registrar"] = registrar[1].strip()

    if creation_date := re.search(r"Creation Date:\s*(.*)", output, re.IGNORECASE):
        info["Creation Date"] = creation_date[1].strip()

    if expiration_date := re.search(r"Registry Expiry Date:\s*(.*)", output, re.IGNORECASE):
        info["Expiration Date"] = expiration_date[1].strip()

    if name_servers := re.findall(r"Name Server:\s*(.*)", output, re.IGNORECASE):
        info["Name Servers"] = ", ".join([ns.strip() for ns in name_servers])

    return info


async def fetch_ip_info(ip_or_domain: str) -> dict | None:
    url = f"https://ipinfo.io/{ip_or_domain}/json"
    async with httpx.AsyncClient(http2=True) as client:
        response = await client.get(url)
        if response.status_code == 200:
            req = response.json()
            req.pop("readme", None)
            return req
        return None


async def fetch_dns_info(hostname: str, record_type: str) -> list[str]:
    url = f"https://cloudflare-dns.com/dns-query?name={hostname}&type={record_type}"
    headers = {"accept": "application/dns-json"}
    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return [
                    i["data"]
                    for i in data.get("Answer", [])
                    if i["type"] == (1 if record_type == "A" else 28)
                ]
        except httpx.HTTPError:
            pass
    return []


async def resolve_hostname(hostname: str) -> list[str]:
    answers: dict[str, list[str]] = {"A": [], "AAAA": []}

    async def fetch(record_type: str) -> None:
        answers[record_type] = await fetch_dns_info(hostname, record_type)

    async with create_task_group() as tg:
        for record_type in ("A", "AAAA"):
            tg.start_soon(fetch, record_type)

    return answers["A"] + answers["AAAA"]


async def get_ips_from_string(hostname: str) -> list[str]:
    try:
        ip = ipaddress.ip_address(hostname)
        return [str(ip)]
    except ValueError:
        parsed = urlparse(hostname)
        host = parsed.hostname or (
            "" if parsed.scheme else urlparse(f"http://{hostname}").hostname
        )
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
