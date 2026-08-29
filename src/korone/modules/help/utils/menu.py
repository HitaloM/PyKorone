from typing import TYPE_CHECKING

from aiogram.enums import ButtonStyle
from aiogram.types import (
    InputRichBlockList,
    InputRichBlockListItem,
    InputRichBlockParagraph,
    InputRichBlockSectionHeading,
    InputRichMessage,
    RichTextCode,
    RichTextItalic,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from korone.modules.help.callbacks import PMHelpModule, PMHelpModules
from korone.modules.help.utils.extract_info import HELP_MODULES
from korone.modules.help.utils.format_help import format_rich_template
from korone.modules.utils_.callbacks import GoToStartCallback
from korone.ui import Bold, Code, Italic, MessageContent, bullets, column, row, section, template
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup, RichTextUnion


def _build_help_menu_buttons(callback_data: PMHelpModules | None) -> InlineKeyboardMarkup:
    modules = sorted(HELP_MODULES.items(), key=lambda item: str(item[1].name))

    buttons = InlineKeyboardBuilder()
    module_buttons_count = 0

    for module_name, module in modules:
        if module.exclude_public:
            continue
        buttons.button(
            text=f"{module.icon} {module.name}",
            callback_data=PMHelpModule(
                module_name=module_name, back_to_start=bool(callback_data and callback_data.back_to_start)
            ),
        )
        module_buttons_count += 1

    has_back_button = bool(callback_data and callback_data.back_to_start)
    if has_back_button:
        buttons.button(text=_("⬅️ Back"), style=ButtonStyle.PRIMARY, callback_data=GoToStartCallback())

    widths = [2] * (module_buttons_count // 2)
    if module_buttons_count % 2:
        widths.append(1)
    if has_back_button:
        widths.append(1)
    if widths:
        buttons.adjust(*widths)

    return buttons.as_markup()


def build_help_menu(callback_data: PMHelpModules | None = None) -> tuple[MessageContent, InlineKeyboardMarkup]:
    doc = column(
        Bold(_("Help")),
        _("Pick a module below to explore its commands, usage notes, and examples."),
        template(_("Search directly with {command}."), command=Code("/help <module>")),
        section(
            _("/help legend"),
            bullets(
                template(
                    _("Arguments: {required} is required, {optional} is optional."),
                    required=Code("<arg>"),
                    optional=Code("<?arg>"),
                ),
                row(Italic(_("— Only in groups")), _("indicates commands available only in groups.")),
                row(Italic(_("PM-only")), _("lists commands available only in private chat.")),
                row(Italic(_("Only admins")), _("lists commands that require admin rights.")),
                row(
                    Italic(template("({label})", label=_("Toggleable"))),
                    template(
                        _("means admins can disable or re-enable the command with {disable} and {enable}."),
                        disable=Code("/disable"),
                        enable=Code("/enable"),
                    ),
                ),
            ),
        ),
    )
    return doc, _build_help_menu_buttons(callback_data)


def _rich_list_item(text: RichTextUnion) -> InputRichBlockListItem:
    return InputRichBlockListItem(blocks=[InputRichBlockParagraph(text=text)])


def build_rich_help_menu(callback_data: PMHelpModules | None = None) -> tuple[InputRichMessage, InlineKeyboardMarkup]:
    legend = InputRichBlockList(
        items=[
            _rich_list_item(
                format_rich_template(
                    _("Arguments: {required} is required, {optional} is optional."),
                    required=RichTextCode(text="<arg>"),
                    optional=RichTextCode(text="<?arg>"),
                )
            ),
            _rich_list_item([
                RichTextItalic(text=str(_("— Only in groups"))),
                " ",
                str(_("indicates commands available only in groups.")),
            ]),
            _rich_list_item([
                RichTextItalic(text=str(_("PM-only"))),
                " ",
                str(_("lists commands available only in private chat.")),
            ]),
            _rich_list_item([
                RichTextItalic(text=str(_("Only admins"))),
                " ",
                str(_("lists commands that require admin rights.")),
            ]),
            _rich_list_item([
                RichTextItalic(text=f"({_('Toggleable')})"),
                " ",
                format_rich_template(
                    _("means admins can disable or re-enable the command with {disable} and {enable}."),
                    disable=RichTextCode(text="/disable"),
                    enable=RichTextCode(text="/enable"),
                ),
            ]),
        ]
    )
    rich_message = InputRichMessage(
        blocks=[
            InputRichBlockSectionHeading(text=str(_("Help")), size=1),
            InputRichBlockParagraph(
                text=str(_("Pick a module below to explore its commands, usage notes, and examples."))
            ),
            InputRichBlockParagraph(
                text=format_rich_template(
                    _("Search directly with {command}."), command=RichTextCode(text="/help <module>")
                )
            ),
            InputRichBlockSectionHeading(text=str(_("/help legend")), size=2),
            legend,
        ]
    )
    return rich_message, _build_help_menu_buttons(callback_data)
