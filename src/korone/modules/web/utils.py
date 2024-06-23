# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import ipaddress
import re
import subprocess

import httpx
from yarl import URL


async def run_whois(domain: str) -> str:
    process = await asyncio.create_subprocess_exec(
        "whois", domain, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        return stdout.decode()

    return stderr.decode()


def parse_whois_output(output: str) -> dict[str, str] | None:
    info = {}

    domain_name = re.search(r"Domain Name:\s*(.*)", output, re.IGNORECASE)
    if domain_name:
        info["Domain Name"] = domain_name.group(1).strip()

    registrar = re.search(r"Registrar:\s*(.*)", output, re.IGNORECASE)
    if registrar:
        info["Registrar"] = registrar.group(1).strip()

    creation_date = re.search(r"Creation Date:\s*(.*)", output, re.IGNORECASE)
    if creation_date:
        info["Creation Date"] = creation_date.group(1).strip()

    expiration_date = re.search(r"Registry Expiry Date:\s*(.*)", output, re.IGNORECASE)
    if expiration_date:
        info["Expiration Date"] = expiration_date.group(1).strip()

    name_servers = re.findall(r"Name Server:\s*(.*)", output, re.IGNORECASE)
    if name_servers:
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
    answers = await asyncio.gather(fetch_dns_info(hostname, "A"), fetch_dns_info(hostname, "AAAA"))
    return [ip for sublist in answers for ip in sublist]


async def get_ips_from_string(hostname: str) -> list[str]:
    try:
        ip = ipaddress.ip_address(hostname)
        return [str(ip)]
    except ValueError:
        parsed = URL(hostname)
        host = parsed.host or (URL(f"http://{hostname}").host if not parsed.is_absolute() else "")
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
