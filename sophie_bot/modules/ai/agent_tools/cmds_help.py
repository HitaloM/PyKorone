from ass_tg.types.base_abc import ArgFabric
from pydantic_ai import RunContext, Tool
from stfu_tg import Doc, Section, KeyValue, VList
from stfu_tg.doc import Element

from sophie_bot.config import CONFIG
from sophie_bot.metrics import track_ai_tool
from sophie_bot.modules.ai.utils.ai_tool_context import SophieAIToolContenxt
from sophie_bot.modules.help.utils.extract_info import HELP_MODULES
from sophie_bot.utils.i18n import gettext as _


def format_ass_arg_data(arg: ArgFabric):
    return Section(_("Can be empty") if arg.can_be_empty else None, title=arg.description)


class CmdsHelpAgentTool:
    @staticmethod
    async def tool_call(ctx: RunContext[SophieAIToolContenxt]) -> str:
        """Extract and format all command and module help information for AI assistant context.

        The returned string is intended for LLM consumption, not for direct user output.
        It provides a structured, human‑readable overview of all modules and their commands, with
        clearly labelled sections and fields so the model can reliably reason about
        available functionality and constraints.
        """
        async with track_ai_tool("cmds_help"):
            if not HELP_MODULES:
                return _("No modules found.")

            doc = Doc(
                _(
                    "SOPHIE BOT HELP CONTEXT\n"
                    "\n"
                    "Commands are organized by module. Each module represents a feature area of the bot.\n"
                    "\n"
                    "Module fields:\n"
                    "  - Name: the human-readable name of the module.\n"
                    "  - Icon: emoji representing the module.\n"
                    "  - Description: what the module does.\n"
                    "  - Info: additional information about the module.\n"
                    "  - Public: whether the module is shown in public listings.\n"
                    "  - Wiki: whether the module has a wiki page.\n"
                    "\n"
                    "Command fields:\n"
                    "  - Commands: slash commands that trigger the handler.\n"
                    "  - Description: human‑readable summary of what the handler does.\n"
                    "  - Arguments: expected arguments (order matters).\n"
                    "  - Context: where the command can be used (PM / groups / both).\n"
                    "  - Permissions: whether admin / OP rights are required.\n"
                    "  - Disableable: name of the feature flag used to disable this command in a chat, if any.\n"
                    "\n"
                )
            )

            modules_sections: list[Element] = []

            # Iterate through each module
            for module_name, module_help in HELP_MODULES.items():
                # Build module information
                module_info_parts = [
                    KeyValue(_("Name"), str(module_help.name)),
                    KeyValue(_("Icon"), module_help.icon),
                ]
                if module_help.description:
                    module_info_parts.append(KeyValue(_("Description"), str(module_help.description)))
                if module_help.info:
                    module_info_parts.append(KeyValue(_("Info"), str(module_help.info)))
                module_info_parts.append(KeyValue(_("Wiki page"), CONFIG.wiki_modules_link + module_name))

                # Build commands list for this module
                commands_elements: list[Element] = []
                if module_help.handlers:
                    for handler in module_help.handlers:
                        commands_elements.append(
                            Section(
                                KeyValue(_("Description"), handler.description) if handler.description else None,
                                Section(
                                    VList(*(format_ass_arg_data(arg) for arg in handler.args.values())),
                                    title=_("Arguments"),
                                )
                                if handler.args
                                else _("This command has no arguments."),
                                _("Can be used only in private chats (PM / DM)") if handler.only_pm else None,
                                _("Can be used only in groups / supergroups") if handler.only_chats else None,
                                _("Can be used in both private chats and groups")
                                if not handler.only_pm and not handler.only_chats
                                else None,
                                _("Can be used only by admins") if handler.only_admin else None,
                                _("Can be used only by OP") if handler.only_op else None,
                                _("No special permissions required")
                                if not handler.only_admin and not handler.only_op
                                else None,
                                KeyValue(_("Disableable"), handler.disableable) if handler.disableable else None,
                                title=" / ".join(f"/{cmd}" for cmd in handler.cmds),
                            )
                        )

                # Combine module info and commands
                module_section_parts = [
                    Section(*module_info_parts, title=_("Module Information")),
                ]
                if commands_elements:
                    module_section_parts.append(Section(*commands_elements, title=_("Commands")))
                else:
                    module_section_parts.append(_("No commands in this module."))

                modules_sections.append(Section(*module_section_parts, title=f"{module_help.icon} {module_name}"))

            md_text = VList(doc, *modules_sections).to_md()
            print(md_text)
            return md_text

    def __new__(cls):
        return Tool(
            cls.tool_call,
            name="cmds_help",
            description="Get information about all available bot modules and commands. Run this before helping users using Sophie.",
            takes_ctx=True,
        )
