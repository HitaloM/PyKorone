from typing import Annotated, Optional

from beanie import Document, Indexed, UpdateResponse
from beanie.odm.operators.find.comparison import In
from beanie.odm.operators.update.array import AddToSet, Pull

from sophie_bot.db.db_exceptions import DBNotFoundException


class DisablingModel(Document):
    # Old ID
    chat_id: Annotated[int, Indexed(unique=True)]

    # New link
    # chat: Link[ChatModel]

    cmds: list[str]

    class Settings:
        name = "disabled"

    @staticmethod
    async def get_disabled(chat_id: int) -> list[str]:
        disabled = await DisablingModel.find_one(DisablingModel.chat_id == chat_id)

        if not disabled:
            return []

        return disabled.cmds

    @staticmethod
    async def disable(chat_id: int, cmd: str) -> "DisablingModel":
        return await DisablingModel.find_one(DisablingModel.chat_id == chat_id).upsert(
            AddToSet({DisablingModel.cmds: cmd}),
            on_insert=DisablingModel(chat_id=chat_id, cmds=[cmd]),
            response_type=UpdateResponse.NEW_DOCUMENT,
        )

    @staticmethod
    async def enable(chat_id: int, cmd: str) -> "DisablingModel":
        model = await DisablingModel.find_one(DisablingModel.chat_id == chat_id, In(DisablingModel.cmds, [cmd]))

        if not model:
            raise DBNotFoundException()

        return await model.update(Pull({DisablingModel.cmds: cmd}))

    @staticmethod
    async def enable_all(chat_id: int) -> Optional["DisablingModel"]:
        model = await DisablingModel.find_one(DisablingModel.chat_id == chat_id)

        if model:
            await model.delete()

        return model
