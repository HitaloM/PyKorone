from sophie_bot.db.models import BetaModeModel, ChatModel, NoteModel
from sophie_bot.db.models.beta import CurrentMode
from sophie_bot.modules.ai.json_schemas.update_note_description import AIUpdateNoteData
from sophie_bot.modules.ai.utils.ai_chatbot import ai_generate_schema
from sophie_bot.modules.ai.utils.message_history import AIMessageHistory
from sophie_bot.modules.utils_.scheduler.chat_language import UseChatLanguage
from sophie_bot.modules.utils_.scheduler.for_chats import ForChats
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.logger import log


class GenerateAITitles:
    @staticmethod
    async def generate_data(note: NoteModel) -> AIUpdateNoteData:
        system_prompt = _(
            "You need to update the data of the chat notes. " "Generate the note data from the provided note text"
        )

        messages = AIMessageHistory()
        messages.add_custom(note.text or "", name=None)
        messages.add_system(system_prompt)

        return await ai_generate_schema(messages, AIUpdateNoteData)

    @staticmethod
    async def update_note(note: NoteModel, generated_data: AIUpdateNoteData):
        note.description = generated_data.description
        note.ai_description = True

        await note.save()

    async def process_chat(self, chat: ChatModel):
        async for note in NoteModel.find(NoteModel.chat_id == chat.chat_id):
            if note.description:
                continue

            generated_data = await self.generate_data(note)
            await self.update_note(note, generated_data)

    async def handle(self):
        async for chat in ForChats():
            status = await BetaModeModel.get_by_chat_id(chat.id)
            if not status:
                log.debug("generate_ai_titles: no mode found, skipping...", chat=chat.id)
                continue

            if status.mode != CurrentMode.beta:
                log.debug("generate_ai_titles: not in beta mode, skipping...", chat=chat.id)
                continue

            async with UseChatLanguage(chat.id):
                await self.process_chat(chat)
