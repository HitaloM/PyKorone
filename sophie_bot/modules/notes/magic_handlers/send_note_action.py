from typing import Any

from aiogram.types import CallbackQuery, Message
from pydantic import BaseModel
from stfu_tg import Bold, Code, HList, Template, Title
from stfu_tg.doc import Element

from sophie_bot.db.models.notes import NoteModel
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.filters.types.modern_action_abc import (
    ActionSetupMessage,
    ActionSetupTryAgainException,
    ModernActionABC,
    ModernActionSetting,
)
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


class SendNoteActionDataModel(BaseModel):
    notename: str


async def setup_confirm(event: Message | CallbackQuery, data: dict[str, Any]) -> SendNoteActionDataModel:
    """Checks given notename and saves it"""
    if isinstance(event, CallbackQuery):
        raise ValueError("This handlers setup_confirm can only be used with messages")

    connection: ChatConnection = data["connection"]
    notename = (event.text or "").split(" ", 1)[0].lower().removeprefix("#")

    # Check whatever given notename exist
    if not (await NoteModel.get_by_notenames(connection.tid, (notename,))):
        await event.reply(_("Note with this name does not exist. Please try again."))
        raise ActionSetupTryAgainException()

    return SendNoteActionDataModel(notename=notename)


async def setup_message(_event: Message | CallbackQuery, _data: dict[str, Any]) -> ActionSetupMessage:
    return ActionSetupMessage(
        text=_("Please write the note name you want to send as a filter trigger."),
    )


class SendNoteAction(ModernActionABC[SendNoteActionDataModel]):
    name = "send_note"

    icon = "🗒"
    title = l_("Send note")

    interactive_setup = ModernActionSetting(
        title=l_("Send note"), setup_message=setup_message, setup_confirm=setup_confirm
    )
    data_object = SendNoteActionDataModel

    @staticmethod
    def description(data: SendNoteActionDataModel) -> Element | str:
        return Template(
            _("Replies to the message with the note with {notename} note name"), notename=Code("#" + data.notename)
        )

    def settings(self, data: SendNoteActionDataModel) -> dict[str, ModernActionSetting]:
        return {
            "send_note": ModernActionSetting(
                title=l_("Change note name"),
                icon="🗒",
                setup_message=setup_message,
                setup_confirm=setup_confirm,
            ),
        }

    async def handle(self, message: Message, data: dict, filter_data: SendNoteActionDataModel):
        connection: ChatConnection = data["connection"]
        notename = filter_data.notename

        note = await NoteModel.get_by_notenames(connection.tid, (notename,))

        if not note:
            await message.reply(_("#{name} note was not found.").format(name=Bold(notename)))
            return

        title = Bold(HList(Title(f"📗 #{notename}", bold=False), _("Filter action")))

        return await common_try(
            send_saveable(
                message,
                message.chat.id,  # Current chat id
                note,
                title=title,
                reply_to=message.message_id,
            )
        )
