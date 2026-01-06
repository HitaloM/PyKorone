from beanie import PydanticObjectId

from sophie_bot.db.models import AIEnabledModel, BetaModeModel, ChatModel, NoteModel
from sophie_bot.db.models.beta import CurrentMode
from sophie_bot.modules.ai.json_schemas.update_note_description import AIUpdateNoteData
from sophie_bot.modules.ai.utils.ai_get_provider import get_chat_default_model
from sophie_bot.modules.ai.utils.new_ai_chatbot import new_ai_generate_schema
from sophie_bot.modules.ai.utils.new_message_history import NewAIMessageHistory
from sophie_bot.modules.utils_.scheduler.chat_language import UseChatLanguage
from sophie_bot.modules.utils_.scheduler.for_chats import ForChats
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log


class GenerateAITitles:
    @staticmethod
    async def generate_data(note: NoteModel, chat_iid: PydanticObjectId) -> AIUpdateNoteData:
        system_prompt = _(
            "You need to update the data of the chat notes. Generate the note data from the provided note text"
        )

        messages = NewAIMessageHistory()
        messages.add_custom(note.text or "", name=None)
        messages.add_system(system_prompt)

        model = await get_chat_default_model(chat_iid)
        return await new_ai_generate_schema(messages, AIUpdateNoteData, model)

    @staticmethod
    async def update_note(note: NoteModel, generated_data: AIUpdateNoteData):
        note.description = generated_data.description
        note.ai_description = True

        await note.save()

    async def process_chat(self, chat: ChatModel):
        log.debug("generate_ai_titles: processing chat", chat=chat)

        chat_notes = NoteModel.find(NoteModel.chat_tid == chat.tid)

        if await chat_notes.count() > 30:
            log.debug("generate_ai_titles: chat has too many notes, skipping...", chat=chat)
            return

        async for note in chat_notes:
            if note.description:
                log.debug("generate_ai_titles: note already has description, skipping...", note=note)
                continue

            if not note.text:
                log.debug("generate_ai_titles: note has no text, skipping...", note=note)

            generated_data = await self.generate_data(note, chat.iid)
            await self.update_note(note, generated_data)

    async def handle(self):
        async for chat in ForChats():
            status = await BetaModeModel.get_by_chat_id(chat.tid)
            if not status:
                log.debug("generate_ai_titles: no mode found, skipping...", chat=chat.tid)
                continue

            if status.mode != CurrentMode.beta:
                log.debug("generate_ai_titles: not in beta mode, skipping...", chat=chat.tid)
                continue

            if not await AIEnabledModel.get_state(chat.tid):
                log.debug("generate_ai_titles: AI features are not enabled, skipping...", chat=chat.tid)

            async with UseChatLanguage(chat.tid):
                await self.process_chat(chat)
