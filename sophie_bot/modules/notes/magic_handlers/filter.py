from aiogram.types import Message
from stfu_tg import Bold, HList, Template, Title

from sophie_bot.db.models import NoteModel
from sophie_bot.db.models.notes import Saveable
from sophie_bot.modules.notes.utils.parse import parse_saveable
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.modules.utils_.common_try import common_try
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

    await send_saveable(
        message,
        current_chat_id,
        note,
        title=title,
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


async def replymsg_filter_handler(message: Message, chat, data):
    saveable = Saveable(**data["reply_text"])

    title = Bold(Title(Template("🪄 {text}", text=_("Reply filter"))))

    return await common_try(
        send_saveable(
            message,
            message.chat.id,
            saveable,
            title=title,
            reply_to=message.message_id,
        )
    )


async def replymsg_setup_start(message: Message):
    await message.edit_text(
        _("Now, please type the text you want to automatically send. It supports buttons and custom formatting.")
    )


async def replymsg_setup_finish(message: Message, data):
    raw_text: str = message.html_text

    saveable: Saveable = await parse_saveable(message, raw_text)
    return {"reply_text": saveable.model_dump(mode="json")}


def get_filter():
    return {
        "reply_message": {
            "title": l_("💭 Reply to message"),
            "handle": replymsg_filter_handler,
            "setup": {"start": replymsg_setup_start, "finish": replymsg_setup_finish},
            "del_btn_name": lambda msg, data: f'Reply to {data["handler"]}: {data["reply_text"].get("text", "None")}" ',
        },
        "get_note": {
            "title": l_("🗒 Send a note"),
            "handle": filter_handle,
            "setup": {"start": setup_start, "finish": setup_finish},
            "del_btn_name": lambda msg, data: f"Get note: {data['note_name']}",
        },
    }
