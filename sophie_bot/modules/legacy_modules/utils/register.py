from aiogram import F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from sophie_bot.filters.chat_status import LegacyOnlyGroups, LegacyOnlyPM
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.message_status import HasArgs, NoArgs
from sophie_bot.filters.user_status import IsAdmin
from sophie_bot.utils.logger import log

REGISTRED_COMMANDS = []
COMMANDS_ALIASES = {}

legacy_modules_router = Router(name="legacy_modules")
legacy_states_router = Router(name="legacy_states")


def register(router: Router, *reg_args, **reg_kwargs):
    if requires_state := "state" in reg_kwargs:
        reg_args = (*reg_args, reg_kwargs["state"])

    if "cmds" in reg_kwargs:
        cmds_list = reg_kwargs["cmds"] if isinstance(reg_kwargs["cmds"], list) else [reg_kwargs["cmds"]]
        reg_args = (CMDFilter(cmds_list), *reg_args)

        for idx, cmd in enumerate(cmds_list):
            if cmd in REGISTRED_COMMANDS:
                log.debug(f"! Legacy @register: Duplication of /{cmd} command")
            REGISTRED_COMMANDS.append(cmd)

            if not idx == len(cmds_list) - 1:
                if cmds_list[0] not in COMMANDS_ALIASES:
                    COMMANDS_ALIASES[cmds_list[0]] = [cmds_list[idx + 1]]
                else:
                    COMMANDS_ALIASES[cmds_list[0]].append(cmds_list[idx + 1])

    if "only_groups" in reg_kwargs:
        reg_args = (*reg_args, LegacyOnlyGroups(True))

    if "no_args" in reg_kwargs:
        reg_args = (*reg_args, NoArgs(True))
    elif "has_args" in reg_kwargs:
        reg_args = (*reg_args, HasArgs(True))

    if "only_pm" in reg_kwargs:
        reg_args = (*reg_args, LegacyOnlyPM(True))

    if "content_types" in reg_kwargs:
        log.error("Legacy @register: content_types filter is not supported")

    if "user_admin" in reg_kwargs or "is_admin" in reg_kwargs:
        reg_args = (*reg_args, IsAdmin(True))

    if "f" in reg_kwargs:
        if reg_kwargs["f"] == "welcome":
            reg_args = (*reg_args, F.new_chat_member)
        elif reg_kwargs["f"] == "leave":
            reg_args = (*reg_args, F.left_chat_member)
        elif reg_kwargs["f"] == "text":
            reg_args = (*reg_args, F.text)
        elif reg_kwargs["f"] == "any":
            # So legacy message handlers that require states can have priority over new modules.
            router = legacy_states_router
        else:
            log.error(f"Legacy @register: Unknown f filter: {reg_kwargs['f']}")

    def wrapper(func):
        async def handler_func(message: Message, state: FSMContext):
            kwargs = {}

            if requires_state:
                kwargs["state"] = state

            await func(message, **kwargs)
            raise SkipHandler

        setattr(handler_func, "aiogram_flag", getattr(func, "aiogram_flag", {}))

        # log.warn(f"Legacy @register: Registering message handler: {reg_args} {reg_kwargs}")
        router.message.register(handler_func, *reg_args)

    return wrapper
