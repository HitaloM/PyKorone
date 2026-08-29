from itertools import starmap
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.filters import CommandObject
from aiogram.types import Message

from korone.args.base import (
    PARSED_ARGUMENTS_KEY,
    ArgumentEntity,
    ArgumentExample,
    ArgumentFieldParsingError,
    ArgumentSchema,
    ArgumentSchemaField,
    ArgumentSource,
    InvalidArgumentError,
    InvalidArgumentValueError,
    MissingArgumentError,
    UnexpectedArgumentError,
)
from korone.ui import Bold, Code, Italic, Renderable, UIExpression, column, field, section, template
from korone.ui.rendering import text_kwargs
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import TelegramObject


def _python_index(text: str, utf16_offset: int) -> int:
    encoded = text.encode("utf-16-le")
    return len(encoded[: utf16_offset * 2].decode("utf-16-le"))


def _command_offset(text: str, command: CommandObject | None) -> int:
    if command is None:
        return 0

    offset = len(command.prefix) + len(command.command)
    if command.mention:
        offset += len(command.mention) + 1
    while offset < len(text) and text[offset].isspace():
        offset += 1
    return offset


def argument_source(message: Message, command: CommandObject | None) -> ArgumentSource:
    if message.text is not None:
        text = message.text
        entities = message.entities or ()
    else:
        text = message.caption or ""
        entities = message.caption_entities or ()
    offset = _command_offset(text, command)

    normalized_entities: list[ArgumentEntity] = []
    for entity in entities:
        start = _python_index(text, entity.offset)
        end = _python_index(text, entity.offset + entity.length)
        if start < offset:
            continue
        normalized_entities.append(
            ArgumentEntity(type=str(entity.type), offset=start - offset, length=end - start, user=entity.user)
        )

    return ArgumentSource(text=text[offset:], entities=tuple(normalized_entities))


def _examples(schema_field: ArgumentSchemaField) -> UIExpression | None:
    examples = schema_field.argument.examples
    if not examples:
        return None
    return section(_("Examples"), *starmap(_format_example, examples.items()))


def _format_example(example: ArgumentExample, description: Renderable | None) -> Renderable:
    content = Code(example) if isinstance(example, str) else example
    if description is None:
        return content
    return field(content, description)


def _argument_name(schema_field: ArgumentSchemaField) -> Renderable:
    return schema_field.argument.description or schema_field.name


def _usage(schema: ArgumentSchema[object], command: CommandObject | None) -> UIExpression:
    signature = []
    if command is not None:
        signature.append(f"{command.prefix}{command.command}")
    signature.extend(f"<{schema_field.help_description}>" for schema_field in schema.fields)
    return section(_("Usage"), Code(" ".join(signature)))


def _field_error_details(
    error: ArgumentFieldParsingError, schema: ArgumentSchema[object], command: CommandObject | None
) -> tuple[UIExpression | None, ...]:
    return (
        section(_("Needed type"), Italic(error.field.argument.needed_type()[0])),
        _examples(error.field),
        _usage(schema, command),
    )


def _format_error(
    error: MissingArgumentError | InvalidArgumentError | InvalidArgumentValueError | UnexpectedArgumentError,
    schema: ArgumentSchema[object],
    command: CommandObject | None,
) -> UIExpression:
    if isinstance(error, MissingArgumentError):
        return column(
            Bold(
                template(
                    _("The required argument {argument} wasn't provided."), argument=Code(_argument_name(error.field))
                )
            ),
            *_field_error_details(error, schema, command),
        )

    if isinstance(error, InvalidArgumentError):
        return column(
            Bold(
                template(_("The argument {argument} has an invalid type."), argument=Code(_argument_name(error.field)))
            ),
            *_field_error_details(error, schema, command),
        )

    if isinstance(error, InvalidArgumentValueError):
        return column(
            Bold(
                template(_("The argument {argument} has an invalid value."), argument=Code(_argument_name(error.field)))
            ),
            *error.messages,
            *_field_error_details(error, schema, command),
        )

    return column(
        Bold(template(_("Unexpected argument: {argument}."), argument=Code(error.remaining))), _usage(schema, command)
    )


class ArgumentsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> object:
        arguments = data["handler"].flags.get("args")
        if arguments is None:
            return await handler(event, data)
        if not isinstance(arguments, ArgumentSchema):
            msg = "The args flag must contain an ArgumentSchema"
            raise TypeError(msg)
        if not isinstance(event, Message):
            msg = "ArgumentsMiddleware only supports Message events"
            raise TypeError(msg)

        command = data.get("command")
        command_object = command if isinstance(command, CommandObject) else None
        source = argument_source(event, command_object)

        try:
            parsed = await arguments.parse(source)
        except (MissingArgumentError, InvalidArgumentError, InvalidArgumentValueError, UnexpectedArgumentError) as exc:
            content = _format_error(exc, arguments, command_object)
            await event.reply(**text_kwargs(content, disable_web_page_preview=True))
            return None

        data[PARSED_ARGUMENTS_KEY] = parsed
        return await handler(event, data)
