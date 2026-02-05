from __future__ import annotations

from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypeVar, cast
from uuid import UUID

from aiogram.filters import Filter
from aiogram.filters.callback_data import _check_field_is_nullable
from pydantic import BaseModel

from korone.config import CONFIG
from korone.constants import TELEGRAM_CALLBACK_DATA_MAX_LENGTH
from korone.filters.cmd import CMDFilter

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.filters import CommandObject
    from aiogram.types import Chat, Message


class CmdStartFilter(Filter):
    __slots__ = ("cmd_start", "start_filter")

    def __init__(self, *, cmd_start: type[CmdStart]) -> None:
        self.start_filter = CMDFilter("start")

        self.cmd_start = cmd_start

    async def __call__(
        self, message: Message, bot: Bot, event_chat: Chat
    ) -> bool | dict[str, CommandObject | CmdStart]:
        command_data: dict[str, CommandObject] | bool = await self.start_filter(
            message=message, bot=bot, event_chat=event_chat
        )
        command: CommandObject | None = command_data.get("command") if isinstance(command_data, dict) else None

        if not command:
            return False

        args = command.args

        if not args:
            return False

        try:
            unpacked = self.cmd_start.unpack(args)
        except TypeError, ValueError:
            return False

        return {"command": command, "command_start": unpacked}


T = TypeVar("T", bound="CmdStart")


class CmdStart(BaseModel):
    __separator__: ClassVar[str] = "_"
    __prefix__: ClassVar[str]

    def __init_subclass__(cls, **kwargs: dict[str, Any]) -> None:
        if "prefix" not in kwargs:
            msg = "prefix required"
            raise ValueError(msg)

        prefix = kwargs.pop("prefix")
        if not isinstance(prefix, str):
            msg = "prefix must be a string"
            raise TypeError(msg)

        cls.__prefix__ = prefix

        super().__init_subclass__(**cast("dict[str, Any]", kwargs))

    @staticmethod
    def _encode_value(key: str, *, value: str | Enum | UUID | bool | float | Decimal | Fraction) -> str:
        if value is None:
            return ""
        if isinstance(value, Enum):
            return str(value.value)
        if isinstance(value, UUID):
            return value.hex
        if isinstance(value, bool):
            return str(int(value))
        if isinstance(value, (int, str, float, Decimal, Fraction)):
            return str(value)
        msg = f"Attribute {key}={value!r} of type {type(value).__name__!r} can not be packed to callback data"
        raise ValueError(msg)

    def pack(self, link_type: str = "start") -> str:
        result = [self.__prefix__]
        for key, value in self.model_dump(mode="json").items():
            encoded = self._encode_value(key, value=value)
            if self.__separator__ in encoded:
                msg = f"Separator symbol {self.__separator__!r} can not be used in value {key}={encoded!r}"
                raise ValueError(msg)
            result.append(encoded)
        data = f"https://t.me/{CONFIG.username}?{link_type}=" + self.__separator__.join(result)

        if len(data.encode()) > TELEGRAM_CALLBACK_DATA_MAX_LENGTH:
            msg = "Too long"
            raise ValueError(msg)

        return data

    @classmethod
    def unpack(cls, value: str) -> Self:
        prefix, *parts = value.split(cls.__separator__)
        names = cls.model_fields.keys()
        if len(parts) != len(names):
            msg = f"CmdStart {cls.__name__!r} takes {len(names)} arguments but {len(parts)} were given"
            raise ValueError(msg)
        if prefix != cls.__prefix__:
            msg = f"Bad prefix ({prefix!r} != {cls.__prefix__!r})"
            raise ValueError(msg)
        payload = {}
        for k, v in zip(names, parts):
            field_value: str | None = (
                None if (field := cls.model_fields.get(k)) and not v and _check_field_is_nullable(field) else v
            )
            payload[k] = field_value
        return cls(**payload)

    @classmethod
    def filter(cls) -> CmdStartFilter:
        return CmdStartFilter(cmd_start=cls)
