from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.handlers import MessageHandler
from ass_tg.types import BooleanArg
from stfu_tg import Bold, Doc, Italic, KeyValue, Section, Template, Url

from sophie_bot import CONFIG
from sophie_bot.db.models.ai_autotranslate import AIAutotranslateModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.message_status import HasArgs
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.ai.texts import AI_POLICY
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(alias_to_modules=["language"], description=l_("Show current state of AI Autotranslate"))
class AIAutotransStatus(MessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter(("aiautotranslate", "autotranslate")), ~ChatTypeFilter("private")

    async def handle(self) -> Any:
        connection: ChatConnection = self.data["connection"]

        if not connection.db_model:
            raise SophieException("Chat has no database model saved.")

        state = await AIAutotranslateModel.get_state(connection.db_model.id)

        doc = Doc(
            Section(
                KeyValue(_("Chat"), connection.title),
                KeyValue(_("Current state"), _("Enabled") if state else _("Disabled")),
                title=_("✨ AI Auto translate"),
            ),
            Template(
                _("By using AI features you agree to the our {policy} and third-party AI provider's."),
                policy=Url(_("privacy policy"), CONFIG.privacy_link),
            ),
            Template(_("Use '{cmd}' to change it."), cmd=Italic("/aiautotranslate (on / off)")),
        )

        await self.event.reply(str(doc), disable_web_page_preview=True)


@flags.args(new_state=BooleanArg(l_("New state")))
@flags.help(alias_to_modules=["language"], description=l_("Controls AI Autotranslate"))
class ControlAIAutotrans(MessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter(("aiautotranslate", "autotranslate")),
            HasArgs(True),
            UserRestricting(admin=True),
            ~ChatTypeFilter("private"),
        )

    async def handle(self) -> Any:
        new_state: bool = self.data["new_state"]
        connection: ChatConnection = self.data["connection"]

        if not connection.db_model:
            raise SophieException("Chat has no database model saved.")

        await AIAutotranslateModel.set_state(connection.db_model, new_state)

        status_text = _("enabled") if new_state else _("disabled")

        doc = Doc(
            Bold(
                Template(
                    _("✨ AI Auto translate have been {status} in {chat}."),
                    status=status_text.lower(),
                    chat=connection.title,
                )
            ),
            (AI_POLICY if new_state else None),
        )

        await self.event.reply(str(doc), disable_web_page_preview=True)
