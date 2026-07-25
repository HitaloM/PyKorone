from inspect import isawaitable
from typing import TYPE_CHECKING, cast, override

from korone.args.base import (
    Argument,
    ArgumentDescription,
    ArgumentEntities,
    ArgumentExample,
    ArgumentExamples,
    ArgumentParseResult,
    ArgumentTypeError,
    ParsedArgument,
)
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from collections.abc import Awaitable


async def resolve_argument[T](result: ArgumentParseResult[T]) -> ParsedArgument[T]:
    if isawaitable(result):
        return await cast("Awaitable[ParsedArgument[T]]", result)
    return result


class TextArg(Argument[str]):
    __slots__ = ()

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("Text"), l_("Text")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {"Foo": None, "Foo Bar": None}

    @override
    def parse(self, text: str, entities: ArgumentEntities) -> ParsedArgument[str]:
        del entities
        if not text:
            raise ArgumentTypeError
        return ParsedArgument(length=len(text), value=text)


class WordArg(Argument[str]):
    __slots__ = ()

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("Word (string with no spaces)"), l_("Words (strings with no spaces)")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {"Hello": None, "Foo": None, "bar": None}

    @override
    def parse(self, text: str, entities: ArgumentEntities) -> ParsedArgument[str]:
        del entities
        word = text.split(maxsplit=1)[0] if text.strip() else ""
        if not word:
            raise ArgumentTypeError
        return ParsedArgument(length=len(word), value=word)


class BooleanArg(Argument[bool]):
    __slots__ = ()

    true_words = frozenset({"true", "t", "1", "yes", "y", "+", "on", "enable", "enabled", ":)"})
    false_words = frozenset({"false", "f", "0", "no", "n", "-", "off", "disable", "disabled", ":("})

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("Boolean (Yes / No value)"), l_("Booleans (Yes / No values)")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {"true": l_("True (can means Enabled or Yes)"), "false": l_("False (can means Disabled or No)")}

    @override
    def parse(self, text: str, entities: ArgumentEntities) -> ParsedArgument[bool]:
        del entities
        word = text.split(maxsplit=1)[0].casefold() if text.strip() else ""
        if word not in self.true_words and word not in self.false_words:
            raise ArgumentTypeError
        return ParsedArgument(length=len(word), value=word in self.true_words)


class OptionalArg[T](Argument[T | None]):
    __slots__ = ("child",)

    can_be_empty = True

    def __init__(self, child: Argument[T]) -> None:
        super().__init__(child.description)
        self.child = child

    @property
    @override
    def help_description(self) -> ArgumentDescription | None:
        if self.description is None:
            return None
        description = self.description
        return LazyProxy(lambda: f"?{description}", enable_cache=False)

    @property
    @override
    def examples(self) -> ArgumentExamples | None:
        return self.child.examples

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        singular, plural = self.child.needed_type()
        return l_("Optional {}").format(singular), l_("Optionals {}").format(plural)

    @override
    async def parse(self, text: str, entities: ArgumentEntities) -> ParsedArgument[T | None]:
        try:
            parsed = await resolve_argument(self.child.parse(text, entities))
        except ArgumentTypeError:
            return ParsedArgument(length=0, value=None)
        return ParsedArgument(length=parsed.length, value=parsed.value)


class OrArg[T](Argument[T]):
    __slots__ = ("arguments",)

    def __init__(self, *arguments: Argument[T], description: ArgumentDescription | None = None) -> None:
        if not arguments:
            msg = "OrArg requires at least one child argument"
            raise ValueError(msg)
        super().__init__(description if description is not None else arguments[0].description)
        self.arguments = arguments

    @property
    @override
    def examples(self) -> ArgumentExamples | None:
        merged: dict[ArgumentExample, ArgumentDescription | None] = {}
        for argument in self.arguments:
            if argument.examples:
                merged.update(argument.examples)
        return merged or None

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        singular = l_(" or ").join(f"'{argument.needed_type()[0]}'" for argument in self.arguments)
        plural = l_(" or ").join(f"'{argument.needed_type()[1]}'" for argument in self.arguments)
        return singular, plural

    @override
    async def parse(self, text: str, entities: ArgumentEntities) -> ParsedArgument[T]:
        for argument in self.arguments:
            try:
                return await resolve_argument(argument.parse(text, entities))
            except ArgumentTypeError:
                continue
        raise ArgumentTypeError
