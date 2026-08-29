from typing import TYPE_CHECKING

from korone.db.repositories.disabling import DisablingRepository
from korone.modules.help.utils.extract_info import DISABLEABLE_CMDS

if TYPE_CHECKING:
    from korone.modules.help.utils.extract_info import HandlerHelp


async def get_disabled_handlers(chat_id: int) -> tuple[HandlerHelp, ...]:
    disabled_cmds = set(await DisablingRepository.get_disabled(chat_id))

    return tuple(cmd for cmd in DISABLEABLE_CMDS if cmd.disableable in disabled_cmds)


def get_cmd_help_by_name(name: str) -> HandlerHelp | None:
    return next((cmd for cmd in DISABLEABLE_CMDS if cmd.disableable == name or name in cmd.cmds), None)
