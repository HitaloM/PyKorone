from typing import Final
from urllib.parse import urlencode

IMAGE_RESIZE_BASE_URL: Final[str] = "https://wsrv.nl/"


def frame_device_image_url(source_url: str) -> str:
    if not source_url:
        return ""

    query = urlencode({
        "url": source_url,
        "w": 1280,
        "h": 720,
        "fit": "contain",
        "cbg": "white",
        "output": "jpg",
        "q": 90,
    })
    return f"{IMAGE_RESIZE_BASE_URL}?{query}"
