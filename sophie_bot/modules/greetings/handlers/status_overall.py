from typing import Any, ClassVar, Dict

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from stfu_tg import Bold, Doc, Italic, KeyValue, Section, Template, Title

from sophie_bot.db.models import GreetingsModel, RulesModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.greetings.default_welcome import get_default_welcome_message
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Shows welcome settings"))
@flags.disableable(name="welcome")
class WelcomeSettingsShowHandler(SophieMessageHandler):
    bool_status: ClassVar[Dict[bool, LazyProxy]] = {True: l_("Yes"), False: l_("No")}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("welcome"),)

    async def handle(self) -> Any:
        connection = self.connection

        db_item: GreetingsModel = await GreetingsModel.get_by_chat_id(connection.tid)

        doc = Doc(
            Section(
                KeyValue(_("Greet new users"), self.bool_status[not db_item.welcome_disabled]),
                KeyValue(
                    _("Clean welcome messages"),
                    self.bool_status[bool(db_item.clean_welcome and db_item.clean_welcome.enabled)],
                ),
                KeyValue(
                    _("Clean service messages"),
                    self.bool_status[bool(db_item.clean_service and db_item.clean_service.enabled)],
                ),
                title=_("Welcome Settings"),
            ),
            Template(_("Use {cmd} to Disable / Enable new users greetings"), cmd=Italic("/enablewelcome")),
            Template(_("Use {cmd} to set custom welcome message"), cmd=Italic("/setwelcome")),
            Template(_("Use {cmd} to retrieve Welcome Security settings"), cmd=Italic("/welcomesecurity")),
            Template(_("Check out {cmd} to learn more about Welcome settings."), cmd=Italic("/help")),
        )
        await self.event.reply(str(doc))

        title = Bold(Title(_("Welcome Message")))

        rules = await RulesModel.get_rules(chat_id=connection.tid)
        additional_fillings = {"rules": rules.text or "" if rules else _("No chat rules, have fun!")}

        welcome = db_item.note or get_default_welcome_message(bool(rules))

        return await send_saveable(
            self.event,
            self.event.chat.id,
            welcome,
            title=title,
            raw=False,
            reply_to=self.event.message_id,
            additional_fillings=additional_fillings,
            connection=connection,
        )
