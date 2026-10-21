import orjson


def dumps_text(value: object) -> str:
    """Serialize JSON for transports that require text instead of bytes."""
    return orjson.dumps(value).decode("utf-8")
