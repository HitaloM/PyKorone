from aiogram import F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from sophie_bot import dp
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.utils.filters.chat_status import OnlyGroups, OnlyPM
from sophie_bot.utils.filters.message_status import NoArgs, HasArgs
from sophie_bot.utils.filters.user_status import IsAdmin
from sophie_bot.utils.logger import log

REGISTRED_COMMANDS = []
COMMANDS_ALIASES = {}


def register(
        *reg_args,
        **reg_kwargs
):
    if requires_state := 'state' in reg_kwargs:
        reg_args = (*reg_args, reg_kwargs['state'])

    if 'cmds' in reg_kwargs:
        cmds_list = reg_kwargs['cmds'] if isinstance(reg_kwargs['cmds'], list) else [reg_kwargs['cmds']]
        reg_args = (CMDFilter(cmds_list), *reg_args)

        for idx, cmd in enumerate(cmds_list):
            if cmd in REGISTRED_COMMANDS:
                log.warn(f'Legacy @register: Duplication of /{cmd} command')
            REGISTRED_COMMANDS.append(cmd)

            if not idx == len(cmds_list) - 1:
                if not cmds_list[0] in COMMANDS_ALIASES:
                    COMMANDS_ALIASES[cmds_list[0]] = [cmds_list[idx + 1]]
                else:
                    COMMANDS_ALIASES[cmds_list[0]].append(cmds_list[idx + 1])

    if 'only_groups' in reg_kwargs:
        reg_args = (*reg_args, OnlyGroups(True))

    if 'no_args' in reg_kwargs:
        reg_args = (*reg_args, NoArgs(True))
    elif 'has_args' in reg_kwargs:
        reg_args = (*reg_args, HasArgs(True))

    if 'only_pm' in reg_kwargs:
        reg_args = (*reg_args, OnlyPM(True))

    if 'content_types' in reg_kwargs:
        log.error('Legacy @register: content_types filter is not supported')

    if 'user_admin' in reg_kwargs:
        reg_args = (*reg_args, IsAdmin(True))

    if 'f' in reg_kwargs:
        if reg_kwargs['f'] == 'welcome':
            reg_args = (*reg_args, F.new_chat_member)
        else:
            log.error(f'Legacy @register: Unknown f filter: {reg_kwargs["f"]}')

    def wrapper(func):
        async def handler_func(message: Message, state: FSMContext):
            kwargs = {}

            if requires_state:
                kwargs["state"] = state

            await func(message, **kwargs)
            raise SkipHandler

        log.warn(f"Legacy @register: Registering message handler: {reg_args}"
                 f" {reg_kwargs}")
        dp.message.register(handler_func, *reg_args)

    return wrapper
