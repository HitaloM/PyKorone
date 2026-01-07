from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ass_tg.entities import ArgEntities

from sophie_bot.db.models.button_action import ButtonAction
from sophie_bot.db.models.notes_buttons import Button
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.SophieButtonABC import AssButtonData
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.parse_arg import ButtonsArg
from sophie_bot.modules.notes.utils.buttons_processor.registry import ASS_MAPPING
from sophie_bot.modules.notes.utils.buttons_processor.unparse import unparse_buttons


class ButtonsList(list[list[Button]]):
    @staticmethod
    def from_ass(buttons: list[AssButtonData]) -> "ButtonsList":
        res = ButtonsList()
        if not buttons:
            return res

        current_row: list[Button] = []
        for ass_button in buttons:
            button = Button(
                text=ass_button.title,
                action=ASS_MAPPING.get(ass_button.button_type, ass_button.button_type),  # type: ignore[arg-type]
                data=ass_button.arguments[0] if ass_button.arguments else None,
            )

            if ass_button.same_row and current_row:
                current_row.append(button)
            else:
                if current_row:
                    res.append(current_row)
                current_row = [button]

        if current_row:
            res.append(current_row)

        return res

    @staticmethod
    def from_markup(markup: InlineKeyboardMarkup) -> "ButtonsList":
        return ButtonsList(*parse_message_buttons(markup))

    @staticmethod
    async def from_text(text: str) -> "ButtonsList":
        entities = ArgEntities([])

        arg = ButtonsArg()
        arg.check(text, entities)
        _, raw_ass = await arg.parse(text, 0, entities)
        return ButtonsList.from_ass(raw_ass)

    def unparse(self, chat_id: int) -> InlineKeyboardMarkup:
        return unparse_buttons(self, chat_id)


class UnknownMessageButtonTypeError(Exception):
    pass


def parse_message_button(button: InlineKeyboardButton) -> Optional[Button]:
    if button.url:
        action = ButtonAction.url
        data = button.url
    else:
        raise UnknownMessageButtonTypeError(button)

    return Button(
        text=button.text,
        action=action,
        data=data,
    )


def parse_message_buttons_row(row: list[InlineKeyboardButton]) -> list[Button]:
    try:
        return list(filter(None, map(parse_message_button, row)))
    except UnknownMessageButtonTypeError:
        return []


def parse_message_buttons(reply_markup: InlineKeyboardMarkup) -> list[list[Button]]:
    return [parsed_row for parsed_row in map(parse_message_buttons_row, reply_markup.inline_keyboard) if parsed_row]
