from aiogram import F
from aiogram.filters import CommandStart
from aiogram.types import Message

from sophie_bot.modules.legacy_modules.utils.connections import chat_connection
from sophie_bot.modules.legacy_modules.utils.disable import disableable_dec
from sophie_bot.modules.legacy_modules.utils.language import get_strings_dec
from sophie_bot.modules.legacy_modules.utils.message import get_args_str
from sophie_bot.modules.legacy_modules.utils.register import register
from sophie_bot.modules.notes.utils.legacy_notes import (
    ALLOWED_COLUMNS,
    BUTTONS,
    get_parsed_note_list,
    send_note,
    t_unparse_note_item,
)
from sophie_bot.services.db import db


@register(cmds=["setrules", "saverules"], user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec("rules")
async def set_rules(message: Message, chat, strings):
    chat_id = chat["chat_id"]

    # FIXME: documents are allow to saved (why?), check for args if no 'reply_to_message'
    note = await get_parsed_note_list(message, allow_reply_message=True, split_args=-1)
    note["chat_id"] = chat_id

    if (await db.rules.replace_one({"chat_id": chat_id}, note, upsert=True)).modified_count > 0:
        text = strings["updated"]
    else:
        text = strings["saved"]

    await message.reply(text % chat["chat_title"])


@register(cmds="rules")
@disableable_dec("rules")
@chat_connection(only_groups=True)
@get_strings_dec("rules")
async def rules(message: Message, chat, strings):
    chat_id = chat["chat_id"]
    send_id = message.chat.id

    if "reply_to_message" in message:
        rpl_id = message.reply_to_message.message_id
    else:
        rpl_id = message.message_id

    if len(args := get_args_str(message).split()) > 0:
        arg1 = args[0].lower()
    else:
        arg1 = None
    noformat = arg1 in ("noformat", "raw")

    if not (db_item := await db.rules.find_one({"chat_id": chat_id})):
        await message.reply(strings["not_found"])
        return

    text, kwargs = await t_unparse_note_item(message, db_item, chat_id, noformat=noformat)
    kwargs["reply_to"] = rpl_id

    await send_note(send_id, text, **kwargs)


@register(cmds="resetrules", user_admin=True)
@chat_connection(admin=True, only_groups=True)
@get_strings_dec("rules")
async def reset_rules(message: Message, chat, strings):
    chat_id = chat["chat_id"]

    if (await db.rules.delete_one({"chat_id": chat_id})).deleted_count < 1:
        await message.reply(strings["not_found"])
        return

    await message.reply(strings["deleted"])


BUTTONS.update({"rules": "btn_rules"})


@register(CommandStart(), F.text.regexp(r"btn_rules"))
@get_strings_dec("rules")
async def rules_btn(message: Message, strings):
    chat_id = (get_args_str(message).split("_"))[2]
    user_id = message.chat.id
    if not (db_item := await db.rules.find_one({"chat_id": int(chat_id)})):
        await message.answer(strings["not_found"])
        return

    text, kwargs = await t_unparse_note_item(message, db_item, chat_id)
    await send_note(user_id, text, **kwargs)


async def __export__(chat_id):
    rules = await db.rules.find_one({"chat_id": chat_id})
    if rules:
        del rules["_id"]
        del rules["chat_id"]

        return {"rules": rules}


async def __import__(chat_id, data):
    rules = data
    for column in [i for i in data if i not in ALLOWED_COLUMNS]:
        del rules[column]

    rules["chat_id"] = chat_id
    await db.rules.replace_one({"chat_id": rules["chat_id"]}, rules, upsert=True)
