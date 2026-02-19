from __future__ import annotations

import re
from html import unescape

from korone.modules.ai.fsm.pm import AI_GENERATED_TEXT
from korone.modules.ai.utils.ai_models import MODEL_SHORT_NAME

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_FALLBACK_AI_HINT = "korone ai"
_TITLEBAR_TRIM_CHARS = " .:-|[]()"


def _plain_text(value: str) -> str:
    without_tags = _HTML_TAG_RE.sub("", value)
    return " ".join(unescape(without_tags).split()).strip()


_AI_HEADER_HINT = _plain_text(str(AI_GENERATED_TEXT)).lower()
_MODEL_SHORT_HINT = MODEL_SHORT_NAME.lower()


def is_ai_message(text: str) -> bool:
    normalized = _plain_text(text).lower()
    if not normalized:
        return False

    if _AI_HEADER_HINT and _AI_HEADER_HINT in normalized:
        return True

    return _FALLBACK_AI_HINT in normalized


def cut_titlebar(text: str) -> str:
    plain = _plain_text(text)
    if not plain:
        return plain

    lowered = plain.lower()
    if _AI_HEADER_HINT not in lowered and _FALLBACK_AI_HINT not in lowered:
        return plain

    result = plain
    if _AI_HEADER_HINT in lowered:
        index = lowered.find(_AI_HEADER_HINT)
        result = result[index + len(_AI_HEADER_HINT) :].strip(_TITLEBAR_TRIM_CHARS)
        lowered = result.lower()

    if lowered.startswith(_MODEL_SHORT_HINT):
        result = result[len(MODEL_SHORT_NAME) :].strip(_TITLEBAR_TRIM_CHARS)

    return result or plain
