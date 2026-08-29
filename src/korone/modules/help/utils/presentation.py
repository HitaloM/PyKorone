from typing import TYPE_CHECKING

from aiogram.enums import ButtonStyle
from aiogram.types import (
    InputRichBlockBlockQuotation,
    InputRichBlockParagraph,
    InputRichBlockSectionHeading,
    InputRichMessage,
    RichTextCode,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.modules.help.callbacks import PMHelpModule, PMHelpModules
from korone.modules.help.utils.extract_info import HELP_MODULES, get_aliased_cmds
from korone.modules.help.utils.format_help import (
    format_rich_examples,
    format_rich_handlers,
    format_rich_template,
    format_rich_text,
    group_handlers,
)
from korone.modules.help.utils.search import search_help_modules
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup, InputRichBlockUnion

    from korone.modules.help.utils.extract_info import ModuleHelp


def build_module_help(module_name: str, module: ModuleHelp) -> InputRichMessage:
    cmds = [handler for handler in module.handlers if not handler.only_op]

    rich_blocks: list[InputRichBlockUnion] = [InputRichBlockSectionHeading(text=f"{module.icon} {module.name}", size=1)]

    if module.description:
        rich_blocks.append(
            InputRichBlockBlockQuotation(blocks=[InputRichBlockParagraph(text=format_rich_text(module.description))])
        )
    if module.info:
        rich_blocks.append(InputRichBlockParagraph(text=format_rich_text(module.info)))

    for section_title, handlers in group_handlers(cmds):
        rich_blocks.extend((
            InputRichBlockSectionHeading(text=str(section_title), size=2),
            format_rich_handlers(handlers),
        ))

    for aliased_module_name, aliased_commands in get_aliased_cmds(module_name).items():
        aliased_module = HELP_MODULES[aliased_module_name]
        rich_blocks.extend((
            InputRichBlockSectionHeading(
                text=format_rich_template(
                    _("Shared commands from {module}"), module=f"{aliased_module.icon} {aliased_module.name}"
                ),
                size=2,
            ),
            format_rich_handlers(aliased_commands),
        ))

    if examples := format_rich_examples(cmds):
        rich_blocks.append(InputRichBlockSectionHeading(text=str(_("Examples")), size=2))
        rich_blocks.extend(examples)

    return InputRichMessage(blocks=rich_blocks)


def build_module_back_button(*, back_to_start: bool = False) -> InlineKeyboardMarkup:
    buttons = InlineKeyboardBuilder()
    buttons.button(
        text=_("⬅️ Back"), style=ButtonStyle.PRIMARY, callback_data=PMHelpModules(back_to_start=back_to_start)
    )
    return buttons.as_markup()


def build_module_search(query: str) -> tuple[InputRichMessage, InlineKeyboardMarkup]:
    result = search_help_modules(query)
    if result.exact is not None:
        module_name, module = result.exact
        return build_module_help(module_name, module), build_module_back_button()

    if result.suggestions:
        paragraph = InputRichBlockParagraph(
            text=format_rich_template(_("Modules matching {query}. Choose one below."), query=RichTextCode(text=query))
        )
    else:
        paragraph = InputRichBlockParagraph(
            text=format_rich_template(_("No modules found for {query}."), query=RichTextCode(text=query))
        )

    rich_message = InputRichMessage(
        blocks=[InputRichBlockSectionHeading(text=str(_("Module search")), size=1), paragraph]
    )
    buttons = InlineKeyboardBuilder()
    for module_name, module in result.suggestions:
        buttons.button(text=f"{module.icon} {module.name}", callback_data=PMHelpModule(module_name=module_name))
    buttons.button(text=_("View all modules"), style=ButtonStyle.PRIMARY, callback_data=PMHelpModules())
    buttons.adjust(*(1 for _ in range(len(result.suggestions) + 1)))
    return rich_message, buttons.as_markup()
