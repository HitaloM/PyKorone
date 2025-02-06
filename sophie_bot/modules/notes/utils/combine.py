from stfu_tg import Doc, PreformattedHTML
from stfu_tg.doc import Element

from sophie_bot.db.models.notes import Saveable, SaveableParseMode
from sophie_bot.modules.notes.utils.unparse_legacy import legacy_markdown_to_html


def combine_saveables(*items: tuple[Saveable, Element]) -> Saveable:
    """This function combines multiple saveables into one."""

    # if len(tuple(saveable.file for saveable, _ in items)) > 1:
    #     # TODO: Allow same type with file group.
    #     raise ValueError("Can't combine multiple saveables with files")

    text = Doc()
    # buttons = InlineKeyboardMarkup(inline_keyboard=[])
    for idx, (saveable, title) in enumerate(items):
        if idx != 0:
            text += " "
        text += title

        # Convert legacy markdown to HTML
        saveable_text = (
            legacy_markdown_to_html(saveable.text or "")
            if text and saveable.parse_mode != SaveableParseMode.html
            else saveable.text
        )

        text += PreformattedHTML(saveable_text)
        # buttons.inline_keyboard.extend(saveable.buttons)

    return Saveable(text=text.to_html(), file=items[0][0].file, parse_mode=SaveableParseMode.html)
