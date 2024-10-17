from aiogram.types import Message
from stfu_tg import Bold, HList, Title

from sophie_bot.db.models import NoteModel
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


async def filter_handle(message: Message, chat, data: dict):
    chat_id = chat["chat_id"]
    note_name: str = data["note_name"]

    current_chat_id = message.chat.id

    note = await NoteModel.get_by_notenames(chat_id, (note_name,))

    if not note:
        await message.reply(_("#{name} note was not found.").format(name=Bold(note_name)))
        return

    title = Bold(HList(Title(f"📗 #{note_name}", bold=False), _("Filter action")))
    legacy_title = HList(Title(f"📙 #{note_name}", bold=False), _("Filter action"))

    await send_saveable(
        message,
        current_chat_id,
        note,
        title=title,
        legacy_title=str(legacy_title),
        reply_to=message.message_id,
    )


async def setup_start(message: Message):
    text = _("Now, please type the note name you want to automatically send.")
    await message.edit_text(text)


async def setup_finish(message: Message, data: dict):
    note_name = (message.text or "").split(" ", 1)[0].split()[0].lower().removeprefix("#")

    chat_id = data["chat_id"]
    note = await NoteModel.get_by_notenames(chat_id, (note_name,))

    if not note:
        await message.reply(_("Cannot find the note with this name. Please make sure it exists and try again."))
        return

    return {"note_name": note_name}


def get_filter():
    return {
        "get_note": {
            "title": l_("🗒 Send a note"),
            "handle": filter_handle,
            "setup": {"start": setup_start, "finish": setup_finish},
            "del_btn_name": lambda msg, data: f"Get note: {data['note_name']}",
        }
    }
