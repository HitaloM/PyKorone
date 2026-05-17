from typing import TYPE_CHECKING

from korone.db.repositories.disabling import DisablingRepository
from korone.modules.help.utils.extract_info import DISABLEABLE_CMDS
from korone.modules.help.utils.extract_info import get_cmd_help_by_name as _get_cmd_help_by_name

if TYPE_CHECKING:
    from korone.modules.help.utils.extract_info import HandlerHelp


async def get_disabled_handlers(chat_id: int) -> tuple[HandlerHelp, ...]:
    disabled_cmds = set(await DisablingRepository.get_disabled(chat_id))

    return tuple(cmd for cmd in DISABLEABLE_CMDS if any(cmd_name in disabled_cmds for cmd_name in cmd.cmds))


def get_cmd_help_by_name(name: str) -> HandlerHelp | None:
    return _get_cmd_help_by_name(name)
