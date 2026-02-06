from __future__ import annotations

import ipaddress
from typing import Any

import asyncwhois

from .misc import _extract_hostname


async def query_whois(domain: str) -> dict[str, Any] | None:
    try:
        _, parsed_dict = await asyncwhois.aio_whois(domain)
    except asyncwhois.NotFoundError:
        return None
    except asyncwhois.QueryError:
        return None
    else:
        return parsed_dict or None


def parse_whois_response(data: dict[str, Any]) -> dict[str, str] | None:
    info: dict[str, str] = {}

    if domain_name := data.get("domain_name"):
        if isinstance(domain_name, list):
            info["Domain Name"] = domain_name[0] if domain_name else ""
        elif isinstance(domain_name, str):
            info["Domain Name"] = domain_name

    if registrar := data.get("registrar"):
        if isinstance(registrar, list):
            info["Registrar"] = registrar[0] if registrar else ""
        elif isinstance(registrar, str):
            info["Registrar"] = registrar

    if created := data.get("created"):
        if isinstance(created, list):
            info["Creation Date"] = str(created[0]) if created else ""
        else:
            info["Creation Date"] = str(created)

    if updated := data.get("updated"):
        if isinstance(updated, list):
            info["Updated Date"] = str(updated[0]) if updated else ""
        else:
            info["Updated Date"] = str(updated)

    if expires := data.get("expires"):
        if isinstance(expires, list):
            info["Expiration Date"] = str(expires[0]) if expires else ""
        else:
            info["Expiration Date"] = str(expires)

    if name_servers := data.get("name_servers"):
        if isinstance(name_servers, list):
            ns_list = [str(ns).lower() for ns in name_servers if ns]
            if ns_list:
                info["Name Servers"] = ", ".join(ns_list)
        elif isinstance(name_servers, str):
            info["Name Servers"] = name_servers.lower()

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

    return None
