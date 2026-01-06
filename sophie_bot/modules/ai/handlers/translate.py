from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.handlers import MessageHandler
from aiogram.types import Message
from ass_tg.types import TextArg
from pydantic_ai import ModelHTTPError
from stfu_tg import (
    BlockQuote,
    Bold,
    Doc,
    HList,
    PreformattedHTML,
    Section,
    Template,
    Title,
)

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.fsm.pm import AI_GENERATED_TEXT
from sophie_bot.modules.ai.json_schemas.translate import AITranslateResponseSchema
from sophie_bot.modules.ai.utils.ai_get_provider import get_chat_translations_model
from sophie_bot.modules.ai.utils.new_ai_chatbot import new_ai_generate_schema
from sophie_bot.modules.ai.utils.new_message_history import NewAIMessageHistory
from sophie_bot.modules.ai.utils.transform_audio import transform_voice_to_text
from sophie_bot.modules.error.utils.capture import capture_sentry
from sophie_bot.modules.error.utils.error_message import generic_error_message
from sophie_bot.modules.notes.utils.unparse_legacy import legacy_markdown_to_html
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.utils.logger import log


async def text_or_reply(message: Message | None, _data: dict):
    if message and message.reply_to_message:
        return {}
    return {
        "text": TextArg(l_("Text to translate")),
    }


@flags.help(
    alias_to_modules=["language"],
    description=l_(
        "Translates the given (or replied) text to the chat's selected language. Also transcribes the "
        "replied voice message to text"
    ),
)
@flags.disableable(name="translate")
@flags.ai_cache(cache_handler_result=True)
class AiTranslate(MessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter(("aitranslate", "translate", "tr")), AIEnabledFilter()

    async def handle(self):
        connection: ChatConnection = self.data["connection"]
        is_autotranslate: bool = self.data.get("autotranslate", False)

        language_name = self.data["i18n"].current_locale_display

        is_voice = False
        if self.event.reply_to_message and self.event.reply_to_message.voice and not is_autotranslate:
            to_translate = await transform_voice_to_text(self.event.reply_to_message.voice)
            is_voice = True
        elif self.event.reply_to_message and not is_autotranslate:
            to_translate = self.event.reply_to_message.text or ""
        elif self.data.get("voice"):
            to_translate = ""
            is_voice = True
        else:
            to_translate = self.data.get("text", "")

        # AI Context
        ai_context = NewAIMessageHistory()
        if self.event.reply_to_message and self.event.reply_to_message.photo:
            ai_context.add_system(
                _("If applicable, translate the photo to {language_name}").format(language_name=language_name)
            )
            await ai_context.add_from_message(self.event.reply_to_message, disable_name=True)

        ai_context.add_system(
            "\n".join(
                (
                    _("You're the professional AI translator / transcriber."),
                    _("Translate the following text to {language_name}:\n{to_translate}").format(
                        language_name=language_name, to_translate=to_translate
                    ),
                    _(
                        "Set translation_explanations to null unless the source is ambiguous,"
                        " self-contradictory, requires culturally/contextually essential explanation,"
                        " contains untranslatable idiom/wordplay/polysemy affecting meaning,"
                        " or needs disambiguation of a proper noun/technical term/abbreviation;"
                        "if included, keep it concise (≤2 factual sentences)."
                    ),
                )
            )
        )

        log.debug("AiTranslate", ai_context=ai_context.history_debug())

        model = await get_chat_translations_model(connection.db_model.iid)

        try:
            translated = await new_ai_generate_schema(ai_context, AITranslateResponseSchema, model=model)
        except ModelHTTPError as err:
            event_id = capture_sentry(err)
            if self.data.get("silent_error"):
                return
            else:
                return self.event.reply(
                    **generic_error_message(err, sentry_event_id=event_id, title=_("Error generating translation"))
                )

        # Prevent extra translating
        if is_autotranslate and not is_voice and not translated.needs_translation:
            log.debug("AiTranslate: AI do not think it needs translation, skipping.")
            return
        elif is_autotranslate and to_translate.lower().strip() == translated.translated_text.lower().strip():
            log.debug("AiTranslate: AI gave the exact same text, skipping.")
            return

        doc = Doc(
            HList(
                Title(AI_GENERATED_TEXT),
                _("Auto Translator") if is_autotranslate else _("Translator"),
                f"({_('Voice')})" if is_voice else None,
            ),
            (
                Bold(
                    Template(
                        _("From {from_lang} to {to_lang}"),
                        from_lang=f"{translated.origin_language_emoji} {translated.origin_language_name}",
                        to_lang=language_name,
                    )
                )
                if not is_voice
                else None
            ),
            BlockQuote(PreformattedHTML(legacy_markdown_to_html(translated.translated_text)), expandable=True),
            (
                Section(translated.translation_explanations, title=_("Translation Notes"))
                if translated.translation_explanations
                else None
            ),
        )

        await self.event.reply(str(doc))
