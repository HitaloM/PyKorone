from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic_ai import RunContext, Tool  # noqa: TC002
from stfu_tg import Doc, KeyValue, Section, VList

from korone.logger import get_logger
from korone.modules.ai.utils.ai_tool_context import KoroneAIToolContext  # noqa: TC001
from korone.modules.help.utils.extract_info import HELP_MODULES
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from ass_tg.types.base_abc import ArgFabric
    from stfu_tg.doc import Element

logger = get_logger(__name__)


def format_ass_arg_data(arg: ArgFabric) -> Element:
    return Section(_("Can be empty") if arg.can_be_empty else None, title=arg.description)


class CmdsHelpAgentTool:
    @staticmethod
    async def tool_call(ctx: RunContext[KoroneAIToolContext]) -> str:
        """Extract and format all command and module help information for AI assistant context."""
        if not HELP_MODULES:
            return _("No modules found.")

        doc = Doc(
            _(
                "KORONE BOT HELP CONTEXT\n"
                "\n"
                "Commands are organized by module. Each module represents a feature area of the bot.\n"
                "\n"
                "Module fields:\n"
                "  - Name: the human-readable name of the module.\n"
                "  - Icon: emoji representing the module.\n"
                "  - Description: what the module does.\n"
                "  - Info: additional information about the module.\n"
                "  - Public: whether the module is shown in public listings.\n"
                "\n"
                "Command fields:\n"
                "  - Commands: slash commands that trigger the handler.\n"
                "  - Description: human-readable summary of what the handler does.\n"
                "  - Arguments: expected arguments (order matters).\n"
                "  - Context: where the command can be used (PM / groups / both).\n"
                "  - Permissions: whether admin / OP rights are required.\n"
                "  - Disableable: name of the feature flag used to disable this command in a chat, if any.\n"
                "\n"
            )
        )

        modules_sections: list[Element] = []
        for module_name, module_help in HELP_MODULES.items():
            module_info_parts: list[Element] = [
                KeyValue(_("Name"), str(module_help.name)),
                KeyValue(_("Icon"), module_help.icon),
            ]
            if module_help.description:
                module_info_parts.append(KeyValue(_("Description"), str(module_help.description)))
            if module_help.info:
                module_info_parts.append(KeyValue(_("Info"), str(module_help.info)))

            commands_elements: list[Element] = [
                Section(
                    KeyValue(_("Description"), handler.description) if handler.description else None,
                    Section(VList(*(format_ass_arg_data(arg) for arg in handler.args.values())), title=_("Arguments"))
                    if handler.args
                    else _("This command has no arguments."),
                    _("Can be used only in private chats (PM / DM)") if handler.only_pm else None,
                    _("Can be used only in groups / supergroups") if handler.only_chats else None,
                    _("Can be used in both private chats and groups")
                    if not handler.only_pm and not handler.only_chats
                    else None,
                    _("Can be used only by admins") if handler.only_admin else None,
                    _("Can be used only by OP") if handler.only_op else None,
                    _("No special permissions required") if not handler.only_admin and not handler.only_op else None,
                    KeyValue(_("Disableable"), handler.disableable) if handler.disableable else None,
                    title=" / ".join(f"/{cmd}" for cmd in handler.cmds),
                )
                for handler in module_help.handlers
            ]

            module_section_parts: list[Element] = [Section(*module_info_parts, title=_("Module Information"))]
            if commands_elements:
                module_section_parts.append(Section(*commands_elements, title=_("Commands")))
            else:
                module_section_parts.append(Section(_("No commands in this module."), title=_("Commands")))

            modules_sections.append(Section(*module_section_parts, title=f"{module_help.icon} {module_name}"))

        md_text = VList(doc, *modules_sections).to_md()
        logger.debug("cmds_help: generated help text", text_length=len(md_text), chat_id=ctx.deps.chat_id)
        return md_text

    def __new__(cls) -> Tool[KoroneAIToolContext]:
        return Tool(
            cls.tool_call,
            name="cmds_help",
            description=(
                "Get information about all available bot modules and commands. "
                "Run this before helping users use Korone commands."
            ),
            takes_ctx=True,
        )
