from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from korone.args import ArgumentDescription, ArgumentValueError, TransformArg, WordArg
from korone.modules.disabling.utils.get_disabled import get_cmd_help_by_name
from korone.ui import Code, template
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from korone.modules.help.utils.extract_info import HandlerHelp


@dataclass(frozen=True, slots=True)
class CommandReference:
    name: str
    disableable_name: str
    handler: HandlerHelp


class CommandArg(TransformArg[str, CommandReference]):
    def __init__(self, description: ArgumentDescription | None = None) -> None:
        super().__init__(WordArg(description))

    @override
    async def transform(self, value: str) -> CommandReference:
        command = value.casefold().removeprefix("/")
        handler = get_cmd_help_by_name(command)
        if handler is None or handler.disableable is None:
            raise ArgumentValueError(template(_("Command {cmd} not found."), cmd=Code(f"/{command}")))
        return CommandReference(name=command, disableable_name=handler.disableable, handler=handler)
