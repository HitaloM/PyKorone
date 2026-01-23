from stfu_tg import Code, KeyValue, Section, Template

from korone.modules.help.utils.extract_info import HELP_MODULES


async def help_stats():
    modules = HELP_MODULES.values()

    return Section(
        Template(
            "{modules} modules has {cmds} commands",
            modules=Code(len(modules)),
            cmds=Code(sum(len(module.handlers) for module in modules)),
        ),
        KeyValue(
            "With arguments definition", Code(sum(sum(1 for cmd in module.handlers if cmd.args) for module in modules))
        ),
        title="Help",
    )
