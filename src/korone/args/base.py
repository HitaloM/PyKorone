from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import MISSING, Field, dataclass, fields, is_dataclass
from typing import TYPE_CHECKING, Protocol, cast

from korone.utils.i18n import LazyProxy

if TYPE_CHECKING:
    from aiogram.types import User

    from korone.ui import MessageContent, Renderable

type ArgumentDescription = str | LazyProxy
type ArgumentExample = Renderable
type ArgumentExamples = Mapping[ArgumentExample, ArgumentDescription | None]
type ArgumentEntities = Sequence[ArgumentEntity]

PARSED_ARGUMENTS_KEY = "_korone_parsed_arguments"
ARGUMENT_HELP_PAYLOAD_KEY = "argument_help_payload"


class _DataclassParams(Protocol):
    frozen: bool


@dataclass(frozen=True, slots=True)
class ArgumentEntity:
    type: str
    offset: int
    length: int
    user: User | None = None


@dataclass(frozen=True, slots=True)
class ArgumentSource:
    text: str
    entities: tuple[ArgumentEntity, ...] = ()

    @property
    def empty(self) -> bool:
        return not self.text

    def lstrip(self) -> ArgumentSource:
        stripped = len(self.text) - len(self.text.lstrip())
        return self.consume(stripped)

    def consume(self, length: int) -> ArgumentSource:
        if not 0 <= length <= len(self.text):
            msg = "Argument consumption is outside the remaining input"
            raise ValueError(msg)
        return ArgumentSource(
            text=self.text[length:],
            entities=tuple(
                ArgumentEntity(type=entity.type, offset=entity.offset - length, length=entity.length, user=entity.user)
                for entity in self.entities
                if entity.offset >= length
            ),
        )


@dataclass(frozen=True, slots=True)
class ParsedArgument[T]:
    consumed: int
    value: T


class ArgumentTypeError(Exception):
    pass


class ArgumentValueError(Exception):
    def __init__(self, *messages: MessageContent) -> None:
        from korone.ui.rendering import plain_text  # ruff: ignore[import-outside-top-level]

        self.messages = messages
        super().__init__(*(plain_text(message) for message in messages))


def _uncached_description(description: ArgumentDescription | None) -> ArgumentDescription | None:
    if not isinstance(description, LazyProxy):
        return description
    return LazyProxy(description._func, *description._args, enable_cache=False, **description._kwargs)


class Argument[T](ABC):
    __slots__ = ("description",)

    consumes_remainder = False

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
    async def parse(self, source: ArgumentSource) -> ParsedArgument[T]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class ArgumentSchemaField:
    name: str
    argument: Argument[object]
    required: bool

    @property
    def help_description(self) -> ArgumentDescription:
        description = self.argument.help_description or self.name
        if self.required:
            return description
        return LazyProxy(lambda: f"?{description}", enable_cache=False)


class ArgumentParsingError(Exception):
    pass


class ArgumentFieldParsingError(ArgumentParsingError):
    def __init__(self, field: ArgumentSchemaField) -> None:
        self.field = field
        super().__init__(field.name)


class MissingArgumentError(ArgumentFieldParsingError):
    pass


class InvalidArgumentError(ArgumentFieldParsingError):
    pass


class InvalidArgumentValueError(ArgumentFieldParsingError):
    def __init__(self, field: ArgumentSchemaField, messages: tuple[MessageContent, ...]) -> None:
        self.messages = messages
        super().__init__(field)


class UnexpectedArgumentError(ArgumentParsingError):
    def __init__(self, remaining: str) -> None:
        self.remaining = remaining
        super().__init__(remaining)


def _is_required(field: Field[object]) -> bool:
    return field.default is MISSING and field.default_factory is MISSING


class ArgumentSchema[T]:
    __slots__ = ("_fields", "model")

    def __init__(self, model: type[T], **arguments: object) -> None:
        if not isinstance(model, type) or not is_dataclass(model):
            msg = "ArgumentSchema model must be a dataclass type"
            raise TypeError(msg)
        dataclass_params = cast("_DataclassParams", getattr(model, "__dataclass_params__"))
        if not dataclass_params.frozen or "__slots__" not in vars(model):
            msg = "ArgumentSchema model must be a frozen, slotted dataclass"
            raise TypeError(msg)

        model_fields = tuple(field for field in fields(model) if field.init)
        expected_names = {field.name for field in model_fields}
        received_names = set(arguments)
        if expected_names != received_names:
            missing = sorted(expected_names - received_names)
            unexpected = sorted(received_names - expected_names)
            details = []
            if missing:
                details.append(f"missing parsers: {', '.join(missing)}")
            if unexpected:
                details.append(f"unknown parsers: {', '.join(unexpected)}")
            msg = f"ArgumentSchema fields do not match the model ({'; '.join(details)})"
            raise TypeError(msg)

        schema_fields: list[ArgumentSchemaField] = []
        optional_seen = False
        for index, model_field in enumerate(model_fields):
            argument = arguments[model_field.name]
            if not isinstance(argument, Argument):
                msg = f"Parser for '{model_field.name}' must be an Argument instance"
                raise TypeError(msg)

            required = _is_required(cast("Field[object]", model_field))
            if required and optional_seen:
                msg = "Required arguments cannot follow optional arguments"
                raise TypeError(msg)
            optional_seen = optional_seen or not required

            if argument.consumes_remainder and index != len(model_fields) - 1:
                msg = f"Remainder-consuming argument '{model_field.name}' must be last"
                raise TypeError(msg)

            schema_fields.append(
                ArgumentSchemaField(
                    name=model_field.name, argument=cast("Argument[object]", argument), required=required
                )
            )

        self.model = model
        self._fields = tuple(schema_fields)

    @property
    def fields(self) -> tuple[ArgumentSchemaField, ...]:
        return self._fields

    async def parse(self, source: ArgumentSource) -> T:
        remaining = source.lstrip()
        values: dict[str, object] = {}

        for field in self._fields:
            remaining = remaining.lstrip()
            if remaining.empty:
                if field.required:
                    raise MissingArgumentError(field)
                continue

            try:
                parsed = await field.argument.parse(remaining)
            except ArgumentTypeError as exc:
                raise InvalidArgumentError(field) from exc
            except ArgumentValueError as exc:
                raise InvalidArgumentValueError(field, exc.messages) from exc

            if not 0 < parsed.consumed <= len(remaining.text):
                msg = f"Parser for '{field.name}' returned an invalid consumed length"
                raise ValueError(msg)

            values[field.name] = parsed.value
            remaining = remaining.consume(parsed.consumed)

        remaining = remaining.lstrip()
        if not remaining.empty:
            raise UnexpectedArgumentError(remaining.text)

        return self.model(**values)
