import itertools
from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.handlers import MessageHandler
from ass_tg.types import TextArg
from stfu_tg import Code, HList, KeyValue, Section, Template

from sophie_bot.db.models.notes import NoteModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.json_schemas.aisave import (
    AISAVE_JSON_SCHEMA,
    AISaveResponseSchema,
)
from sophie_bot.modules.ai.utils.ai_chatbot import ai_response, build_history
from sophie_bot.modules.ai.utils.message_history import get_message_history
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(
    prompt=TextArg(l_("Prompt")),
)
@flags.help(alias_to_modules=["notes"], description=l_("Generate a new note using AI"))
class AISaveNote(MessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("aisave"), UserRestricting(admin=True), AIEnabledFilter()

    async def handle(self) -> Any:
        connection = self.data["connection"]

        message = await self.event.reply(_("✨ Generating..."))

        all_notes = await NoteModel.get_chat_notes(connection.id)
        all_notenames = list(itertools.chain.from_iterable(note.names for note in all_notes))
        all_groups = list(note.note_group for note in all_notes if note.note_group)

        data: AISaveResponseSchema = await self.make_request(all_notenames, all_groups)

        # Pre-saving checks
        if await NoteModel.get_by_notenames(connection.id, data.notenames):
            return await message.edit_text(_("AI Generation failed, note already exists! Please try again."))

        await self.save(connection.id, data)

        await message.edit_text(
            str(
                Section(
                    KeyValue("Note names", HList(*(f"#{note}" for note in data.notenames))),
                    KeyValue("Description", data.description),
                    title=_("✨ Note was successfully generated"),
                )
                + Template(
                    _("Use {cmd} to retrieve this note."),
                    cmd=Code(f"#{data.notenames[0]}"),
                )
            )
        )

    @staticmethod
    async def save(chat_id: int, data: AISaveResponseSchema) -> bool:
        model = NoteModel(
            chat_id=chat_id,
            names=tuple(data.notenames),
            note_group=data.group,
            description=data.description,
            text=data.text,
        )
        return await model.save()  # type: ignore

    @staticmethod
    def parse_data(data: str) -> AISaveResponseSchema:
        return AISaveResponseSchema.model_validate_json(data)

    async def make_request(self, all_notenames: list[str], all_groups: list[str]) -> AISaveResponseSchema:
        prompt = (
            f"{self.data['prompt']}. Already existing note groups: {', '.join(all_groups)}. NO NOT USE NOTENAMES:"
            f" {', '.join(all_notenames)}"
        )

        history = build_history(
            user_text=prompt,
            additional_history=await get_message_history(self.event),
            user_name=self.event.from_user.full_name if self.event.from_user else "Unknown",
        )
        return self.parse_data(
            await ai_response(history, json_schema={"type": "json_schema", "json_schema": AISAVE_JSON_SCHEMA})  # type: ignore
        )
