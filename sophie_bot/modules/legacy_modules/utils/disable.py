from magic_filter import AttrDict

from sophie_bot.utils.logger import log


def disableable_dec(command):
    log.debug(f"Legacy @disableable_dec: Adding {command} to the disableable commands...")

    def wrapped(func):

        flags = getattr(func, "aiogram_flag", AttrDict())
        flags["disableable"] = AttrDict({"name": command})
        setattr(func, "aiogram_flag", flags)

        return func

    return wrapped
