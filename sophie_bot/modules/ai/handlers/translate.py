from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.handlers import MessageHandler
from aiogram.types import Message
from ass_tg.types import TextArg
from stfu_tg import Bold, Template

from sophie_bot import bot
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.utils.ai_chatbot import ai_reply
from sophie_bot.modules.ai.utils.message_history import MessageHistory
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


async def text_or_reply(message: Message | None, _data: dict):
    if message and message.reply_to_message:
        return {}
    return {
        "text": TextArg(l_("Text to translate")),
    }


@flags.help(
    alias_to_modules=["language"],
    description=l_("Translates the given (or replied) text to the chat's selected language"),
)
@flags.disableable(name="translate")
@flags.ai_cache(cache_handler_result=True)
class AiTranslate(MessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter(("aitranslate", "translate", "tr")), AIEnabledFilter()

    async def handle(self):
        is_autotranslate: bool = self.data.get("autotranslate", False)
        await bot.send_chat_action(self.event.chat.id, "typing")

        language_name = self.data["i18n"].current_locale_display

        if self.event.reply_to_message and not is_autotranslate:
            to_translate = self.event.reply_to_message.text or ""
        else:
            to_translate = self.data.get("text", "")

        system_prompt = "".join(
            (
                _("You're the professional AI translator, try to translate the texts word to word."),
                _("If it needs any explanations or clarifications, write them briefly afterwards separately."),
            )
        )
        user_prompt = _(f"Translate the following text to {language_name}:\n{to_translate}")

        ai_context = await MessageHistory.chatbot(
            self.event, additional_system_prompt=system_prompt, custom_user_text=user_prompt, add_cached_messages=False
        )

        if is_autotranslate:
            header_items = [_("Auto Translator")]
        else:
            header_items = [_("Translator")]

        doc_items = [Bold(Template(_("Translated to {language}"), language=language_name))]

        return await ai_reply(self.event, ai_context, header_items=header_items, doc_items=doc_items)
