from typing import TYPE_CHECKING

from korone.db.repositories.disabling import DisablingRepository
from korone.modules.help.utils.extract_info import get_all_cmds

if TYPE_CHECKING:
    from korone.modules.help.utils.extract_info import HandlerHelp


async def get_disabled_handlers(chat_id: int) -> tuple[HandlerHelp, ...]:
    disabled_cmds: list[str] = await DisablingRepository.get_disabled(chat_id)

    help_cmds: list[HandlerHelp] = list(filter(lambda cmd: cmd.disableable, get_all_cmds()))

    return tuple(cmd for cmd in help_cmds if any(cmd_cmds in disabled_cmds for cmd_cmds in cmd.cmds))


def get_cmd_help_by_name(name: str) -> HandlerHelp | None:
    disable_able_cmds = [cmd for cmd in get_all_cmds() if cmd.disableable]
    return next((handler for handler in disable_able_cmds if name in handler.cmds), None)
