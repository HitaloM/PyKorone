from aiogram import flags
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from ass_tg.types import BooleanArg
from stfu_tg import Section, KeyValue

from sophie_bot import CONFIG
from sophie_bot.db.cache.beta import cache_get_chat_beta
from sophie_bot.db.models import BetaModeModel


@flags.args(
    new_state=BooleanArg("Set beta status"),
)
async def set_beta_state(message: Message, new_state: bool):
    await BetaModeModel.set_state(message.chat.id, new_state)
    await cache_get_chat_beta.reset_cache(message.chat.id)

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Sophie Support",
                callback_data=CONFIG.support_link,
            )
        ]
    ])

    await message.reply(str(Section(
        KeyValue("New status", "Enabled" if new_state else "Disabled"),
        "Please keep in mind, that Beta mode can have bugs and issues. Report your findings to the support chat" if
        new_state else None,
        title="Beta status changed",
    )), reply_markup=buttons if new_state else None)


async def show_beta_state(message):
    beta_state = await cache_get_chat_beta(message.chat.id)
    await message.reply(str(Section(
        KeyValue("Beta status", "Enabled" if beta_state else "Disabled"),
        title="Beta status",
    )))
