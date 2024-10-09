from magic_filter import AttrDict

from sophie_bot.utils.logger import log

LEGACY_DISABLABLE_COMMANDS = []


def disableable_dec(command):
    log.warn(f"Legacy @disableable_dec: Adding {command} to the disableable commands...")

    if command not in LEGACY_DISABLABLE_COMMANDS:
        LEGACY_DISABLABLE_COMMANDS.append(command)

    def wrapped(func):

        flags = getattr(func, "aiogram_flag", AttrDict())
        flags["disableable"] = AttrDict({"name": command})
        setattr(func, "aiogram_flag", flags)

        return func

    return wrapped
