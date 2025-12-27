from __future__ import annotations

from typing import Optional

from unidecode import unidecode


def normalize(text: str | None) -> Optional[str]:
    """
    Normalize the given text by transliterating it to ASCII,
    converting it to lowercase, and collapsing multiple spaces.
    """
    if not text:
        return None

    # Transliterate to ASCII
    text = unidecode(text)

    # Lowercase
    text = text.lower()

    # Collapse multiple spaces and trim
    text = " ".join(text.split())

    return text or None
