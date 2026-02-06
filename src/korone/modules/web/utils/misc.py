from urllib.parse import urlparse


def _extract_hostname(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.hostname:
        return parsed.hostname
    if parsed.scheme:
        return None
    parsed = urlparse(f"http://{value}")
    return parsed.hostname
