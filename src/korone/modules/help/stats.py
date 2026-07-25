from korone.modules.help.utils.extract_info import HELP_MODULES
from korone.utils.formatting import Code, KeyValue, Section, Template


def help_stats() -> Section:
    modules = HELP_MODULES.values()

    return Section(
        Template(
            "{modules} modules has {cmds} commands",
            modules=Code(len(HELP_MODULES)),
            cmds=Code(sum(len(module.handlers) for module in modules)),
        ),
        KeyValue(
            "With arguments definition", Code(sum(sum(1 for cmd in module.handlers if cmd.args) for module in modules))
        ),
        title="Help",
    )
