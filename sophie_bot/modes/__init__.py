import sys
from enum import Enum


class SophieModes(str, Enum):
    bot = "bot"
    scheduler = "scheduler"
    nostart = "nostart"


SOPHIE_MODE: str = SophieModes.nostart

args = sys.argv
if len(args) > 1:
    SOPHIE_MODE = args[1]

if SOPHIE_MODE not in SophieModes.__members__:
    raise ValueError(f"Unknown mode: {SOPHIE_MODE}")
