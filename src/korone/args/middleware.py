from collections.abc import Awaitable, Callable, Mapping
from typing import TYPE_CHECKING, Any, cast

from aiogram import BaseMiddleware
from aiogram.filters import CommandObject

from korone.args.base import Argument, ArgumentEntities, ArgumentEntity, ArgumentTypeError, ArgumentValueError
from korone.args.types import resolve_argument
from korone.utils.formatting import Bold, Code, Doc, Italic, KeyValue, Section
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.types import Message, TelegramObject


def _argument_entities(message: Message, command: CommandObject | None) -> tuple[ArgumentEntity, ...]:
    source = message.entities or message.caption_entities or ()
    command_offset = 0
    if command:
        command_offset = len(command.prefix) + len(command.command)
        if command.mention:
            command_offset += len(command.mention) + 1

        text = message.text or message.caption or ""
        while command_offset < len(text) and text[command_offset].isspace():
            command_offset += 1

    return tuple(
        ArgumentEntity(
            type=str(entity.type), offset=entity.offset - command_offset, length=entity.length, user=entity.user
        )
        for entity in source
        if entity.offset >= command_offset
    )


def _shift_entities(entities: ArgumentEntities, offset: int) -> tuple[ArgumentEntity, ...]:
    return tuple(
        ArgumentEntity(type=entity.type, offset=entity.offset - offset, length=entity.length, user=entity.user)
        for entity in entities
        if entity.offset >= offset
    )


def _examples(argument: Argument[object]) -> Section | None:
    if not argument.examples:
        return None
    return Section(
        *(
            KeyValue(Code(example), description) if description is not None else Code(example)
            for example, description in argument.examples.items()
        ),
        title=_("Examples"),
    )


def _required_error(argument: Argument[object]) -> Doc:
    description = f"({argument.description})" if argument.description else ""
    doc = Doc(
        Bold(_("The required argument {description} wasn't provided!").format(description=description)),
        Section(Italic(argument.needed_type()[0]), title=_("Needed type")),
    )
    doc += _examples(argument)
    return doc


def _type_error(argument: Argument[object]) -> Doc:
    description = f"({argument.description})" if argument.description else ""
    doc = Doc(
        Bold(_("The argument {description} has an invalid type").format(description=description)),
        Section(Italic(argument.needed_type()[0]), title=_("Needed type")),
    )
    doc += _examples(argument)
    return doc


class ArgumentsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> object:
        arguments = data["handler"].flags.get("args")
        if not arguments:
            return await handler(event, data)
        if not isinstance(arguments, Mapping):
            msg = "The args flag must be a mapping"
            raise TypeError(msg)

        message = cast("Message", event)
        command = data.get("command")
        command_object = command if isinstance(command, CommandObject) else None
        remaining = (command_object.args or "") if command_object else (message.text or message.caption or "")
        entities = _argument_entities(message, command_object)

        for name, argument in arguments.items():
            if not isinstance(name, str) or not isinstance(argument, Argument):
                msg = "The args flag must map argument names to Argument instances"
                raise TypeError(msg)

            stripped = len(remaining) - len(remaining.lstrip())
            remaining = remaining.lstrip()
            entities = _shift_entities(entities, stripped)

            if not remaining and not argument.can_be_empty:
                await message.reply(str(_required_error(argument)), disable_web_page_preview=True)
                return None

            try:
                parsed = await resolve_argument(argument.parse(remaining, entities))
            except ArgumentTypeError:
                await message.reply(str(_type_error(argument)), disable_web_page_preview=True)
                return None
            except ArgumentValueError as exc:
                await message.reply(str(Doc(*exc.messages)), disable_web_page_preview=True)
                return None

            data[name] = parsed.value
            remaining = remaining[parsed.length :]
            entities = _shift_entities(entities, parsed.length)

        return await handler(event, data)
