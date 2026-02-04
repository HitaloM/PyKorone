import base64

from aiogram.filters.callback_data import CallbackData


class GetIPCallback(CallbackData, prefix="web_ip"):
    ip: str


def encode_ip(value: str) -> str:
    data = value.encode("utf-8")
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def decode_ip(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    data = base64.urlsafe_b64decode(value + padding)
    return data.decode("utf-8")
