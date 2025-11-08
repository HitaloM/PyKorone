from datetime import timedelta
from typing import Annotated, Optional

from beanie import Document, Indexed
from pydantic import BaseModel

from sophie_bot.db.models.notes import Saveable


class CleanWelcome(BaseModel):
    enabled: bool = False
    last_msg: Optional[int] = None


class CleanService(BaseModel):
    enabled: bool = False


WELCOMEMUTE_DEFALT_VALUE = "48h"
WELCOMESECURITY_EXPIRE_DEFALT_VALUE = "48h"


class WelcomeMute(BaseModel):
    enabled: bool = False
    time: Optional[str | timedelta] = WELCOMEMUTE_DEFALT_VALUE  # TODO: convert to datetime


class WelcomeSecurity(BaseModel):
    enabled: bool = False
    expire: Optional[str] = WELCOMESECURITY_EXPIRE_DEFALT_VALUE  # TODO: convert to datetime


class GreetingsModel(Document):
    # Old ID
    chat_id: Annotated[int, Indexed()]

    welcome_disabled: Optional[bool] = False

    note: Optional[Saveable] = None
    security_note: Optional[Saveable] = None
    join_request_message: Optional[Saveable] = None

    clean_welcome: Optional[CleanWelcome] = CleanWelcome()
    clean_service: Optional[CleanService] = CleanService()

    welcome_mute: Optional[WelcomeMute] = WelcomeMute()
    welcome_security: Optional[WelcomeSecurity] = WelcomeSecurity()

    class Settings:
        name = "greetings"

    @staticmethod
    async def get_by_chat_id(chat_id: int) -> "GreetingsModel":
        return await GreetingsModel.find_one(GreetingsModel.chat_id == chat_id) or GreetingsModel(chat_id=chat_id)

    @staticmethod
    async def change_state_welcome(chat_id: int, new_state: bool) -> "GreetingsModel":
        model = await GreetingsModel.get_by_chat_id(chat_id)
        model.welcome_disabled = not new_state
        return await model.save()

    @staticmethod
    async def change_welcome_message(chat_id: int, saveable: Saveable) -> "GreetingsModel":
        model = await GreetingsModel.get_by_chat_id(chat_id)
        model.note = saveable
        return await model.save()

    @staticmethod
    async def change_join_request_message(chat_id: int, saveable: Saveable) -> "GreetingsModel":
        model = await GreetingsModel.get_by_chat_id(chat_id)
        model.join_request_message = saveable
        return await model.save()

    async def set_clean_welcome_status(self, new_state: bool) -> "GreetingsModel":
        if not self.clean_welcome:
            self.clean_welcome = CleanWelcome(enabled=new_state)
        else:
            self.clean_welcome.enabled = new_state
        return await self.save()

    async def set_service_clean_status(self, new_state: bool) -> "GreetingsModel":
        if not self.clean_welcome:
            self.clean_service = CleanService(enabled=new_state)
        else:
            self.clean_service.enabled = new_state  # type: ignore
        return await self.save()

    async def clean_welcome_new_message(self, msg_id: int) -> "GreetingsModel":
        if not self.clean_welcome:
            self.clean_welcome = CleanWelcome(last_msg=msg_id)
        else:
            self.clean_welcome.last_msg = msg_id
        return await self.save()

    async def set_status_welcomesecurity(self, new_state: bool) -> "GreetingsModel":
        if not self.welcome_security:
            self.welcome_security = WelcomeSecurity(enabled=new_state)
        else:
            self.welcome_security.enabled = new_state
        return await self.save()

    async def set_status_welcomemute(self, new_state: bool, time: Optional[str]) -> "GreetingsModel":
        if not self.welcome_mute:
            self.welcome_mute = WelcomeMute(enabled=new_state, time=time)
        else:
            self.welcome_mute.enabled = new_state

            if time:
                self.welcome_mute.time = time
        return await self.save()
