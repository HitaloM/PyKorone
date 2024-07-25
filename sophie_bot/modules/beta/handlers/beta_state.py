from aiogram import flags
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from ass_tg.types import OneOf
from stfu_tg import Italic, KeyValue, Section, Template

from sophie_bot import CONFIG
from sophie_bot.db.models.beta import BetaModeModel, CurrentMode, PreferredMode
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_

mode_names = {
    "auto": l_("Auto"),
    "stable": l_("Stable"),
    "beta": l_("Beta"),
}


@flags.args(
    new_state=OneOf(("auto", "stable", "beta"), l_("Preferred strategy mode")),
)
@flags.help(description=l_("Set preferred strategy mode"))
async def set_preferred_mode(message: Message, new_state: str):
    state = PreferredMode[new_state]

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
                KeyValue("New strategy", mode_names[state.name]),
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


@flags.help(description=l_("Get current strategy mode / current state"))
async def show_beta_state(message):
    if not (beta_state := await BetaModeModel.get_by_chat_id(message.chat.id)):
        await message.reply(_("Couldn't find the beta state for this chat. Please check it later."))
        return

    preferred_mode = PreferredMode(beta_state.preferred_mode) if beta_state.preferred_mode else PreferredMode.auto
    current_mode = CurrentMode(beta_state.mode) if beta_state.mode else preferred_mode

    await message.reply(
        str(
            Section(
                KeyValue("Preferred mode", mode_names[preferred_mode.name]),
                KeyValue("Current mode", mode_names[current_mode.name]),
                title="Beta mode information",
            )
            + Template(_("Use '{cmd}' to change it."), cmd=Italic("/enablebeta (auto / stable / beta)")),
        )
    )
