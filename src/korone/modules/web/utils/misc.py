from urllib.parse import urldefrag, urlparse, urlsplit, urlunsplit

from url_normalize import url_normalize


def _extract_hostname(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.hostname:
        return parsed.hostname
    if parsed.scheme:
        return None
    parsed = urlparse(f"http://{value}")
    return parsed.hostname


def normalize_url(value: str) -> str | None:
    if not (candidate := value.strip()):
        return None

    try:
        normalized = url_normalize(candidate, default_scheme="https", filter_params=True)
    except ValueError:
        return None

    if not normalized:
        return None

    without_fragment, _ = urldefrag(normalized)
    parsed = urlsplit(without_fragment)
    if not parsed.netloc:
        return None

    path = parsed.path
    if path and path != "/":
        path = path.rstrip("/")
    if not path:
        path = "/"

    return urlunsplit(parsed._replace(path=path))
