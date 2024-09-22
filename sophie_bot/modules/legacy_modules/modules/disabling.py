from aiogram import F, Router, flags
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from ass_tg.types import TextArg

from sophie_bot import dp
from sophie_bot.modules.legacy_modules.utils.connections import chat_connection
from sophie_bot.modules.legacy_modules.utils.disable import (
    DISABLABLE_COMMANDS,
    disableable_dec,
)
from sophie_bot.modules.legacy_modules.utils.language import get_strings_dec
from sophie_bot.modules.legacy_modules.utils.message import get_arg, need_args_dec
from sophie_bot.modules.legacy_modules.utils.register import COMMANDS_ALIASES, register
from sophie_bot.services.db import db
from sophie_bot.utils.i18n import lazy_gettext as l_

__module_name__ = l_("Disabling")
__module_emoji__ = "🚫"

router = Router(name="disabling")


@register(router, cmds="disableable")
@flags.help(description=l_("Lists all commands that can be disabled."))
@disableable_dec("disableable")
@get_strings_dec("disable")
async def list_disablable(message: Message, strings):
    text = strings["disablable"]
    for command in DISABLABLE_COMMANDS:
        text += f"* <code>/{command}</code>\n"
    await message.reply(text)


@register(router, cmds="disabled")
@flags.help(description=l_("Lists all disabled commands."))
@chat_connection(only_groups=True)
@get_strings_dec("disable")
async def list_disabled(message: Message, chat, strings):
    text = strings["disabled_list"].format(chat_name=chat["chat_title"])

    if not (disabled := await db.disabled.find_one({"chat_id": chat["chat_id"]})):
        await message.reply(strings["no_disabled_cmds"].format(chat_name=chat["chat_title"]))
        return

    commands = disabled["cmds"]
    for command in commands:
        text += f"* <code>/{command}</code>\n"
    await message.reply(text)


@register(router, cmds="disable", user_admin=True)
@flags.help(description=l_("Disables the command."), args={"cmd": TextArg(l_("Command"))})
@need_args_dec()
@chat_connection(admin=True, only_groups=True)
@get_strings_dec("disable")
async def disable_command(message: Message, chat, strings):
    cmd = get_arg(message).lower()
    if cmd[0] == "/" or cmd[0] == "!":
        cmd = cmd[1:]

    # Check on commands aliases
    for name, keys in COMMANDS_ALIASES.items():
        if cmd in keys:
            cmd = name
            break

    if cmd not in DISABLABLE_COMMANDS:
        await message.reply(strings["wot_to_disable"])
        return

    if await db.disabled.find_one({"chat_id": chat["chat_id"], "cmds": {"$in": [cmd]}}):
        await message.reply(strings["already_disabled"])
        return

    await db.disabled.update_one(
        {"chat_id": chat["chat_id"]},
        {"$addToSet": {"cmds": {"$each": [cmd]}}},
        upsert=True,
    )

    await message.reply(strings["disabled"].format(cmd=cmd, chat_name=chat["chat_title"]))


@register(router, cmds="enable")
@flags.help(description=l_("Enables the command."), args={"cmd": TextArg(l_("Command"))})
@need_args_dec()
@chat_connection(admin=True, only_groups=True)
@get_strings_dec("disable")
async def enable_command(message: Message, chat, strings):
    chat_id = chat["chat_id"]
    cmd = get_arg(message).lower()
    if cmd[0] == "/" or cmd[0] == "!":
        cmd = cmd[1:]

    # Check on commands aliases
    for name, keys in COMMANDS_ALIASES.items():
        if cmd in keys:
            cmd = name
            break

    if cmd not in DISABLABLE_COMMANDS:
        await message.reply(strings["wot_to_enable"])
        return

    if not await db.disabled.find_one({"chat_id": chat["chat_id"], "cmds": {"$in": [cmd]}}):
        await message.reply(strings["already_enabled"])
        return

    await db.disabled.update_one({"chat_id": chat_id}, {"$pull": {"cmds": cmd}})

    await message.reply(strings["enabled"].format(cmd=cmd, chat_name=chat["chat_title"]))


@register(router, cmds="enableall", is_admin=True)
@flags.help(description=l_("Enables all previously disabled commands"))
@chat_connection(admin=True, only_groups=True)
@get_strings_dec("disable")
async def enable_all(message: Message, chat, strings):
    # Ensure that something is disabled
    if not await db.disabled.find_one({"chat_id": chat["chat_id"]}):
        await message.reply(strings["not_disabled_anything"].format(chat_title=chat["chat_title"]))
        return

    text = strings["enable_all_text"].format(chat_name=chat["chat_title"])
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=strings["enable_all_btn_yes"], callback_data="enable_all_notes_cb")],
        ]
    )
    await message.reply(text, reply_markup=buttons)


@dp.callback_query(F.data.regexp("enable_all_notes_cb"))
@chat_connection(admin=True)
@get_strings_dec("disable")
async def enable_all_notes_cb(event, chat, strings, **kwargs):
    data = await db.disabled.find_one({"chat_id": chat["chat_id"]})
    await db.disabled.delete_one({"_id": data["_id"]})

    text = strings["enable_all_done"].format(num=len(data["cmds"]), chat_name=chat["chat_title"])
    await event.message.edit_text(text)


async def __export__(chat_id):
    disabled = await db.disabled.find_one({"chat_id": chat_id})

    return {"disabling": disabled["cmds"] if disabled else []}


async def __import__(chat_id, data):
    new = []
    for cmd in data:
        if cmd not in DISABLABLE_COMMANDS:
            continue

        new.append(cmd)

    await db.disabled.update_one({"chat_id": chat_id}, {"$set": {"cmds": new}}, upsert=True)
