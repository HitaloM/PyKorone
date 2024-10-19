from aiogram.utils.text_decorations import HtmlDecoration

from sophie_bot.modules.notes.utils.legacy_markdown import parse


def legacy_markdown_to_html(text: str) -> str:
    text, entities = parse(text)

    return HtmlDecoration().unparse(text, entities)
