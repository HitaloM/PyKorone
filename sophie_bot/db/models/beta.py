from asyncio import Lock
from enum import Enum
from typing import Optional

from beanie import Document, UpdateResponse, Indexed
from beanie.odm.operators.update.general import Set, Unset


class PreferredMode(Enum):
    auto = 0
    stable = 1
    beta = 2


class CurrentMode(Enum):
    stable = 1
    beta = 2


class BetaModeModel(Document):
    chat_id: int = Indexed(unique=False)
    preferred_mode: PreferredMode = PreferredMode.auto
    mode: Optional[CurrentMode] = None

    class Settings:
        name = "beta_mode"

    @staticmethod
    async def all_chats_reset_current_mode():
        await BetaModeModel.find(BetaModeModel.mode != None).update(Set({BetaModeModel.mode: None}))  # noqa: E711

    @staticmethod
    async def beta_mode_chats_count():
        return await BetaModeModel.find(BetaModeModel.mode == CurrentMode.beta).count()

    @staticmethod
    async def set_mode(chat_id: int, new_mode: CurrentMode) -> "BetaModeModel":
        async with Lock():
            return await BetaModeModel.find_one(BetaModeModel.chat_id == chat_id).upsert(
                Set({BetaModeModel.mode: new_mode}),
                on_insert=BetaModeModel(
                    chat_id=chat_id,
                    mode=new_mode,
                ),
                response_type=UpdateResponse.NEW_DOCUMENT,
            )

    @staticmethod
    async def set_preferred_mode(chat_id: int, new_mode: PreferredMode) -> "BetaModeModel":
        return await BetaModeModel.find_one(BetaModeModel.chat_id == chat_id).upsert(
            Set({BetaModeModel.preferred_mode: new_mode}),
            Unset({BetaModeModel.mode: 1}),
            on_insert=BetaModeModel(
                chat_id=chat_id,
                preferred_mode=new_mode,
            ),
            response_type=UpdateResponse.NEW_DOCUMENT,
        )

    @staticmethod
    async def get_by_chat_id(chat_id: int) -> Optional["BetaModeModel"]:
        return await BetaModeModel.find_one(BetaModeModel.chat_id == chat_id)
