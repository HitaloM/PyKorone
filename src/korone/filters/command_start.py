from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import Any, ClassVar, Optional, Type, TypeVar, Union
from uuid import UUID

from aiogram import Bot
from aiogram.filters import CommandObject, Filter
from aiogram.filters.callback_data import _check_field_is_nullable
from aiogram.types import Chat, Message
from pydantic import BaseModel

from korone.config import CONFIG
from korone.constants import TELEGRAM_CALLBACK_DATA_MAX_LENGTH
from korone.filters.cmd import CMDFilter


class CmdStartFilter(Filter):
    __slots__ = ("start_filter", "cmd_start")

    def __init__(self, *, cmd_start: Type["CmdStart"]):
        self.start_filter = CMDFilter("start")

        self.cmd_start = cmd_start

    async def __call__(self, message: Message, bot: Bot, event_chat: Chat) -> Union[bool, dict[str, Any]]:
        command_data: dict[str, CommandObject] | bool = await self.start_filter(
            message=message, bot=bot, event_chat=event_chat
        )
        command: Optional[CommandObject] = command_data.get("command") if isinstance(command_data, dict) else None

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

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if "prefix" not in kwargs:
            raise ValueError("prefix required")

        cls.__prefix__ = kwargs.pop("prefix")

        super().__init_subclass__(**kwargs)

    def _encode_value(self, key: str, value: Any) -> str:
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
        raise ValueError(
            f"Attribute {key}={value!r} of type {type(value).__name__!r} can not be packed to callback data"
        )

    def pack(self, link_type: str = "start") -> str:
        result = [self.__prefix__]
        for key, value in self.model_dump(mode="json").items():
            encoded = self._encode_value(key, value)
            if self.__separator__ in encoded:
                raise ValueError(f"Separator symbol {self.__separator__!r} can not be used in value {key}={encoded!r}")
            result.append(encoded)
        data = f"https://t.me/{CONFIG.username}?{link_type}=" + self.__separator__.join(result)

        if len(data.encode()) > TELEGRAM_CALLBACK_DATA_MAX_LENGTH:
            raise ValueError("Too long")

        return data

    @classmethod
    def unpack(cls: Type[T], value: str) -> T:
        prefix, *parts = value.split(cls.__separator__)
        names = cls.model_fields.keys()
        if len(parts) != len(names):
            raise ValueError(f"CmdStart {cls.__name__!r} takes {len(names)} arguments but {len(parts)} were given")
        if prefix != cls.__prefix__:
            raise ValueError(f"Bad prefix ({prefix!r} != {cls.__prefix__!r})")
        payload = {}
        for k, v in zip(names, parts):  # type: str, Optional[str]
            if field := cls.model_fields.get(k):
                if v == "" and _check_field_is_nullable(field):
                    v = None
            payload[k] = v
        return cls(**payload)

    @classmethod
    def filter(cls) -> CmdStartFilter:
        return CmdStartFilter(cmd_start=cls)
