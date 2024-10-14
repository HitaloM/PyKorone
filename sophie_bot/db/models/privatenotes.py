from typing import Annotated

from beanie import Document, Indexed


class PrivateNotesModel(Document):
    # Old ID
    chat_id: Annotated[int, Indexed(unique=True)]

    class Settings:
        name = "privatenotes"

    @staticmethod
    async def get_state(chat_id: int) -> bool:
        return bool(await PrivateNotesModel.find_one(PrivateNotesModel.chat_id == chat_id))

    @staticmethod
    async def set_state(chat_id: int, new_state: bool):
        model = await PrivateNotesModel.find_one(PrivateNotesModel.chat_id == chat_id)
        if model and not new_state:
            return await model.delete()

        elif model:
            return model

        model = PrivateNotesModel(chat_id=chat_id)
        return await model.save()
