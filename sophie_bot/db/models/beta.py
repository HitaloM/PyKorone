from beanie import Document


class BetaModeModel(Document):
    chat_id: int

    class Settings:
        name = "beta_mode"

    @staticmethod
    async def set_state(chat_id: int, state: bool):
        model = await BetaModeModel.find_one(BetaModeModel.chat_id == chat_id)
        if state and not model:
            await BetaModeModel(chat_id=chat_id).insert()
        elif model:
            await model.delete()
