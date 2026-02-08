import asyncio
import ipaddress
import re

from .misc import _extract_hostname


def normalize_domain(value: str) -> str | None:
    if not value:
        return None

    host = _extract_hostname(value)
    if not host:
        return None

    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        return None

    domain_pattern = re.compile(
        r"^(?=.{1,253}$)"
        r"([a-zA-Z0-9-]{1,63}\.)*"
        r"[a-zA-Z0-9-]{1,63}"
        r"(?<!-)$"
    )

    if not domain_pattern.match(host):
        return None

    if "." not in host and host != "localhost":
        return None

    labels = host.split(".")
    for label in labels:
        if not label or len(label) > 63:
            return None
        if label.startswith("-") or label.endswith("-"):
            return None

    if labels[-1].isdigit():
        return None

    return host.lower()


async def query_whois(domain: str) -> str:
    process = await asyncio.create_subprocess_exec(
        "whois", domain, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, _ = await process.communicate()
    return stdout.decode("utf-8")


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
