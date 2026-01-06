from aiogram import flags
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from ass_tg.types import OneOf
from stfu_tg import Italic, KeyValue, Section, Template

from sophie_bot.config import CONFIG
from sophie_bot.db.models import GlobalSettings
from sophie_bot.db.models.beta import BetaModeModel, PreferredMode
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
    beta_state = await BetaModeModel.get_by_chat_id(message.chat.iid)

    preferred_mode = PreferredMode(beta_state.preferred_mode) if beta_state else PreferredMode.auto

    gs_beta_db = await GlobalSettings.get_by_key("beta_percentage")
    percentage = int(gs_beta_db.value) if gs_beta_db else 0

    if beta_state and beta_state.mode:
        current_mode_text = mode_names[beta_state.mode.name]
    elif percentage == 0:
        current_mode_text = mode_names[PreferredMode.stable.name]
    else:
        current_mode_text = l_("Unknown")

    await message.reply(
        str(
            Section(
                KeyValue("Preferred mode", mode_names[preferred_mode.name]),
                KeyValue("Current mode", current_mode_text),
                title="Beta mode information",
            )
            + Template(_("Use '{cmd}' to change it."), cmd=Italic("/enablebeta (auto / stable / beta)")),
        )
    )
