from stfu_tg import Code, KeyValue, Section, Template

from sophie_bot.modules.info.utils.extract_info import HELP_MODULES


async def __stats__():
    modules = HELP_MODULES.values()

    return Section(
        Template(
            "{modules} modules has {cmds} commands",
            modules=Code(len(modules)),
            cmds=Code(sum(len(module.cmds) for module in modules)),
        ),
        KeyValue(
            "With arguments definition", Code(sum(sum(1 for cmd in module.cmds if cmd.args) for module in modules))
        ),
        title="Help",
    )
