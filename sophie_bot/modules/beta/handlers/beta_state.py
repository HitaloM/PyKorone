from aiogram import flags
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from ass_tg.types import OneOf
from stfu_tg import KeyValue, Section

from sophie_bot import CONFIG
from sophie_bot.db.cache.beta import cache_get_chat_beta
from sophie_bot.db.models.beta import BetaModeModel, PreferredMode
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as _l


@flags.args(
    new_state=OneOf(("auto", "stable", "beta"), _l("Preferred strategy mode")),
)
async def set_preferred_mode(message: Message, new_state: str):
    match new_state:
        case "stable":
            state = PreferredMode.stable
            state_text = _("stable")
        case "beta":
            state = PreferredMode.beta
            state_text = _("beta")
        case "auto":
            state = PreferredMode.auto
            state_text = _("auto")
        case _:
            raise SophieException("Unknown strategy mode after ASS validation!")

    await BetaModeModel.set_preferred_mode(message.chat.id, state)

    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Sophie Support",
                    url=CONFIG.support_link,
                )
            ]
        ]
    )

    await message.reply(
        str(
            Section(
                KeyValue("New strategy", state_text),
                (
                    (
                        "Please keep in mind, that Beta mode can have bugs and issues."
                        " Report your findings to the support chat"
                        if new_state
                        else None
                    )
                    if state == PreferredMode.beta
                    else None
                ),
                (
                    "Preferred mode can not always match the current state due to development and rollout progress."
                    if state != PreferredMode.auto
                    else None
                ),
                title="Preferred mode changed",
            )
        ),
        reply_markup=buttons,
    )


async def show_beta_state(message):
    beta_state = await cache_get_chat_beta(message.chat.id)
    await message.reply(
        str(
            Section(
                KeyValue("Beta status", "Enabled" if beta_state else "Disabled"),
                title="Beta status",
            )
        )
    )
