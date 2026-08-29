from dataclasses import dataclass

from korone.args import ArgumentSchema, TextArg
from korone.utils.i18n import lazy_gettext as l_


@dataclass(frozen=True, slots=True)
class HelpArguments:
    query: str | None = None


HELP_ARGUMENTS = ArgumentSchema(HelpArguments, query=TextArg(l_("Module")))
