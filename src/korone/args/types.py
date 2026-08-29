from abc import ABC, abstractmethod
from typing import override

from korone.args.base import (
    Argument,
    ArgumentDescription,
    ArgumentExample,
    ArgumentExamples,
    ArgumentSource,
    ArgumentTypeError,
    ParsedArgument,
)
from korone.utils.i18n import lazy_gettext as l_


class TextArg(Argument[str]):
    __slots__ = ()

    consumes_remainder = True

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("Text"), l_("Text")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {"Foo": None, "Foo Bar": None}

    @override
    async def parse(self, source: ArgumentSource) -> ParsedArgument[str]:
        if source.empty:
            raise ArgumentTypeError
        return ParsedArgument(consumed=len(source.text), value=source.text.rstrip())


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
    async def parse(self, source: ArgumentSource) -> ParsedArgument[str]:
        word = source.text.split(maxsplit=1)[0] if source.text else ""
        if not word:
            raise ArgumentTypeError
        return ParsedArgument(consumed=len(word), value=word)


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
    async def parse(self, source: ArgumentSource) -> ParsedArgument[bool]:
        word = source.text.split(maxsplit=1)[0].casefold() if source.text else ""
        if word not in self.true_words and word not in self.false_words:
            raise ArgumentTypeError
        return ParsedArgument(consumed=len(word), value=word in self.true_words)


class TransformArg[InputT, OutputT](Argument[OutputT], ABC):
    __slots__ = ("child", "consumes_remainder")

    def __init__(self, child: Argument[InputT]) -> None:
        super().__init__(child.description)
        self.child = child
        self.consumes_remainder = child.consumes_remainder

    @property
    @override
    def examples(self) -> ArgumentExamples | None:
        return self.child.examples

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return self.child.needed_type()

    @abstractmethod
    async def transform(self, value: InputT) -> OutputT:
        raise NotImplementedError

    @override
    async def parse(self, source: ArgumentSource) -> ParsedArgument[OutputT]:
        parsed = await self.child.parse(source)
        return ParsedArgument(consumed=parsed.consumed, value=await self.transform(parsed.value))


class OrArg[T](Argument[T]):
    __slots__ = ("arguments", "consumes_remainder")

    def __init__(self, *arguments: Argument[T], description: ArgumentDescription | None = None) -> None:
        if not arguments:
            msg = "OrArg requires at least one child argument"
            raise ValueError(msg)
        super().__init__(description if description is not None else arguments[0].description)
        self.arguments = arguments
        self.consumes_remainder = any(argument.consumes_remainder for argument in arguments)

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
    async def parse(self, source: ArgumentSource) -> ParsedArgument[T]:
        for argument in self.arguments:
            try:
                return await argument.parse(source)
            except ArgumentTypeError:
                continue
        raise ArgumentTypeError
