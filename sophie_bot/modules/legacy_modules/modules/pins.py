from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message

from sophie_bot import bot
from sophie_bot.filters.admin_rights import BotHasPermissions, UserRestricting
from sophie_bot.modules.legacy_modules.utils.connections import chat_connection
from sophie_bot.modules.legacy_modules.utils.language import get_strings_dec
from sophie_bot.modules.legacy_modules.utils.message import get_arg
from sophie_bot.modules.legacy_modules.utils.register import register

router = Router(name="pins")


@register(
    router,
    UserRestricting(can_restrict_members=True),
    BotHasPermissions(can_pin_messages=True),
    cmds="unpin",
)
@chat_connection(admin=True)
@get_strings_dec("pins")
async def unpin_message(message: Message, chat, strings):
    # support unpinning all
    if get_arg(message) in {"all"}:
        return await bot.unpin_all_chat_messages(chat["chat_id"])

    try:
        await bot.unpin_chat_message(chat["chat_id"])
    except TelegramBadRequest:
        await message.reply(strings["chat_not_modified_unpin"])
        return


@register(
    router,
    UserRestricting(can_restrict_members=True),
    BotHasPermissions(can_pin_messages=True),
    cmds="pin",
)
@get_strings_dec("pins")
async def pin_message(message: Message, strings):
    if not message.reply_to_message:
        await message.reply(strings["no_reply_msg"])
        return
    msg = message.reply_to_message.message_id
    arg = get_arg(message).lower()

    dnd = True
    loud = ["loud", "notify"]
    if arg in loud:
        dnd = False

    try:
        await bot.pin_chat_message(message.chat.id, msg, disable_notification=dnd)
    except TelegramBadRequest:
        await message.reply(strings["chat_not_modified_pin"])
