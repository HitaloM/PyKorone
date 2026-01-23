from dataclasses import replace
from typing import List, Optional, Pattern, Sequence, Union, cast

from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.filters.command import CommandException, CommandObject
from aiogram.types import Chat, Message, MessageEntity
from magic_filter import MagicFilter

from korone.config import CONFIG

CMD_TYPE = Union[str, Pattern]


class CMDFilter(BaseFilter):
    __slots__ = (
        "cmd",
        "prefix",
        "ignore_case",
        "ignore_mention",
        "ignore_code",
        "ignore_forwarded",
        "allow_caption",
        "magic",
    )

    def __init__(
        self,
        cmd: Union[Sequence[CMD_TYPE], CMD_TYPE],
        prefix: str = CONFIG.commands_prefix,
        ignore_case: bool = CONFIG.commands_ignore_case,
        ignore_mention: bool = CONFIG.commands_ignore_mention,
        ignore_code: bool = CONFIG.commands_ignore_code,
        ignore_forwarded: bool = CONFIG.commands_ignore_forwarded,
        allow_caption: bool = False,
        magic: Optional[MagicFilter] = None,
    ):
        self.cmd = (cmd,) if type(cmd) is str else cmd
        self.prefix = prefix
        self.ignore_case = ignore_case
        self.ignore_mention = ignore_mention
        self.ignore_code = ignore_code
        self.ignore_forwarded = ignore_forwarded
        self.allow_caption = allow_caption
        self.magic = magic

    @staticmethod
    def extract_command(text: str) -> CommandObject:
        try:
            full_command, *args = text.split(" ", maxsplit=1)
        except ValueError:
            raise CommandException("not enough values to unpack")

        if not full_command:
            raise CommandException("empty command")

        prefix, (command, _, mention) = full_command[0], full_command[1:].partition("@")
        return CommandObject(prefix=prefix, command=command, mention=mention, args=args[0] if args else None)

    def validate_prefix(self, command: CommandObject) -> None:
        if command.prefix not in self.prefix:
            raise CommandException("Invalid command prefix")

    async def validate_mention(self, bot: Bot, command: CommandObject) -> None:
        if command.mention and not self.ignore_mention:
            me = await bot.me()
            if me.username and command.mention.lower() != me.username.lower():
                raise CommandException("Mention did not match")

    def validate_command(self, command: CommandObject) -> CommandObject:
        for allowed_command in cast(Sequence[CMD_TYPE], self.cmd):
            if isinstance(allowed_command, Pattern):
                if result := allowed_command.match(command.command):
                    return replace(command, regexp_match=result)
            elif command.command == allowed_command:
                return command
        raise CommandException("Command did not match pattern")

    def do_magic(self, command: CommandObject) -> None:
        if not self.magic:
            return
        if not self.magic.resolve(command):
            raise CommandException("Rejected via magic filter")

    async def parse_command(self, text: str, bot: Bot) -> CommandObject:
        command = self.extract_command(text)
        self.validate_prefix(command=command)
        await self.validate_mention(bot=bot, command=command)
        command = self.validate_command(command)
        self.do_magic(command=command)
        return command

    @staticmethod
    def check_mono(entities: List[MessageEntity]) -> bool:
        return any((ent for ent in entities if ent.offset == 0 and ent.type in {"code", "pre"}))

    async def __call__(self, message: Message, bot: Bot, event_chat: Chat) -> Union[bool, dict[str, CommandObject]]:
        if not (text := ((message.text or message.caption) if self.allow_caption else message.text)):
            return False

        if self.ignore_forwarded and message.forward_from:
            return False

        if message.entities and self.ignore_code and self.check_mono(message.entities):
            return False

        try:
            return {"command": await self.parse_command(text=text, bot=bot)}
        except CommandException:
            return False

    class Config:
        arbitrary_types_allowed = True
