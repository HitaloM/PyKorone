from asyncio import sleep
from datetime import datetime, timedelta

from sophie_bot.db.models import AIEnabledModel, ChatModel, NoteModel
from sophie_bot.middlewares import i18n
from sophie_bot.modules.ai.json_schemas.update_note_description import AIUpdateNoteData
from sophie_bot.modules.ai.utils.ai_get_provider import get_chat_default_model
from sophie_bot.modules.ai.utils.new_ai_chatbot import new_ai_generate_schema
from sophie_bot.modules.ai.utils.new_message_history import NewAIMessageHistory
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log


class NotesDescriptionsScheduler:
    async def handle(self):
        await sleep(5)

        with i18n.use_locale("en_US"), i18n.context():
            log.debug("NotesDescriptionsScheduler: starting scheduler")
            while True:
                await sleep(5)

                delta = datetime.now() - timedelta(days=1)
                async for chat in ChatModel.find(ChatModel.last_saw >= delta):
                    await sleep(5)

                    if not await AIEnabledModel.get_state(chat.tid):
                        log.debug("- NotesDescriptionsScheduler: AI features are not enabled, skipping...", chat=chat)
                        continue

                    log.debug("NotesDescriptionsScheduler: processing chat", chat=chat)

                    async for note in NoteModel.find(NoteModel.chat_tid == chat.tid):
                        notenames = note.names

                        if note.description:
                            log.debug(
                                "- NotesDescriptionsScheduler: note already has description, skipping...",
                                notenames=notenames,
                            )
                            continue

                        if not note.text:
                            log.debug(
                                "- NotesDescriptionsScheduler: note has no text, skipping...", notenames=notenames
                            )
                            continue

                        log.debug("- NotesDescriptionsScheduler: processing note", notenames=notenames)

                        system_prompt = _(
                            "You need to update the data of the chat notes. "
                            "Generate the note data from the provided note text"
                        )

                        messages = NewAIMessageHistory()
                        messages.add_system(system_prompt)
                        messages.add_custom(note.text, name=None)

                        model = await get_chat_default_model(chat.iid)
                        generated_data = await new_ai_generate_schema(messages, AIUpdateNoteData, model)
                        log.debug("- NotesDescriptionsScheduler: generated data", generated_data=generated_data)

                        note.description = generated_data.description
                        note.ai_description = True

                        await note.save()
                        log.debug("- NotesDescriptionsScheduler: updated!")
