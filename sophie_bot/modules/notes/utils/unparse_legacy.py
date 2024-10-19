from aiogram.utils.text_decorations import HtmlDecoration

from sophie_bot.modules.notes.utils.extract_markdown_entities import (
    extract_markdown_entities,
)


def legacy_markdown_to_html(text: str) -> str:
    text, entities = extract_markdown_entities(text)

    return HtmlDecoration().unparse(text, entities)
