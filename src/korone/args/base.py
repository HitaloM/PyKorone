from abc import ABC, abstractmethod
from collections.abc import Awaitable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, cast

from korone.utils.i18n import LazyProxy

if TYPE_CHECKING:
    from aiogram.types import User

    from korone.utils.formatting import Element

type ArgumentDescription = str | LazyProxy
type ArgumentExample = str | Element
type ArgumentExamples = Mapping[ArgumentExample, ArgumentDescription | None]
type ArgumentParseResult[T] = ParsedArgument[T] | Awaitable[ParsedArgument[T]]
type ArgumentsMap = Mapping[str, Argument[object]]


def define_arguments(**arguments: object) -> ArgumentsMap:
    if not all(isinstance(argument, Argument) for argument in arguments.values()):
        msg = "All declared arguments must be Argument instances"
        raise TypeError(msg)
    return cast("ArgumentsMap", MappingProxyType(arguments))


@dataclass(frozen=True, slots=True)
class ArgumentEntity:
    type: str
    offset: int
    length: int
    user: User | None = None


type ArgumentEntities = Sequence[ArgumentEntity]


@dataclass(frozen=True, slots=True)
class ParsedArgument[T]:
    length: int
    value: T


class ArgumentTypeError(Exception):
    pass


class ArgumentValueError(Exception):
    def __init__(self, *messages: str | Element) -> None:
        self.messages = messages
        super().__init__(*(str(message) for message in messages))


def _uncached_description(description: ArgumentDescription | None) -> ArgumentDescription | None:
    if not isinstance(description, LazyProxy):
        return description
    return LazyProxy(description._func, *description._args, enable_cache=False, **description._kwargs)


class Argument[T](ABC):
    __slots__ = ("description",)

    can_be_empty = False

    def __init__(self, description: ArgumentDescription | None = None) -> None:
        self.description = _uncached_description(description)

    @property
    def help_description(self) -> ArgumentDescription | None:
        return self.description

    @property
    def examples(self) -> ArgumentExamples | None:
        return None

    @abstractmethod
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        raise NotImplementedError

    @abstractmethod
    def parse(self, text: str, entities: ArgumentEntities) -> ArgumentParseResult[T]:
        raise NotImplementedError
