from aiogram.types import Message
from stfu_tg import Bold, HList, Section, Title

from sophie_bot.db.models import RulesModel
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


async def send_chat_rules(message: Message, chat, data):
    rules = await RulesModel.get_rules(message.chat.id)

    if not rules:
        return await message.reply(str(Section(_("No rules are set for this chat."), title=_("Rules filter failed"))))

    title = Bold(HList(Title(f"🪧 {_('Rules')}"), _("Filter action")))

    await send_saveable(
        message,
        message.chat.id,
        rules,
        title=title,
        reply_to=message.message_id,
    )


def get_filter():
    return {
        "send_rules": {"title": l_("🪧 Send chat rules"), "handle": send_chat_rules},
    }
