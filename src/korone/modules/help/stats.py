from korone.modules.help.utils.extract_info import HELP_MODULES
from korone.ui import Code, UIExpression, field, section, template


def help_stats() -> UIExpression:
    modules = HELP_MODULES.values()

    return section(
        "Help",
        template(
            "{modules} modules has {cmds} commands",
            modules=Code(len(HELP_MODULES)),
            cmds=Code(sum(len(module.handlers) for module in modules)),
        ),
        field(
            "With arguments definition", Code(sum(sum(1 for cmd in module.handlers if cmd.args) for module in modules))
        ),
    )
