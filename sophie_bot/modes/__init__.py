from enum import Enum

from sophie_bot import CONFIG


class SophieModes(str, Enum):
    bot = "bot"
    scheduler = "scheduler"
    nostart = "nostart"


SOPHIE_MODE: str = CONFIG.mode

if SOPHIE_MODE not in SophieModes.__members__:
    raise ValueError(f"Unknown mode: {SOPHIE_MODE}")
