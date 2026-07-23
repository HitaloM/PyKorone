from typing import TYPE_CHECKING

from aiogram.enums import ButtonStyle
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Code, Doc, HList, Italic, Section, Template, Title, VList

from korone.modules.help.callbacks import PMHelpModule, PMHelpModules
from korone.modules.help.utils.extract_info import HELP_MODULES
from korone.modules.utils_.callbacks import GoToStartCallback
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.types import InlineKeyboardMarkup


def build_help_menu(callback_data: PMHelpModules | None = None) -> tuple[str, InlineKeyboardMarkup]:
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

    doc = Doc(
        Title(_("Help")),
        _("Pick a module below to explore its commands, usage notes, and examples."),
        Section(
            VList(
                Template(
                    _("Arguments: {required} is required, {optional} is optional."),
                    required=Code("<arg>"),
                    optional=Code("<?arg>"),
                ),
                HList(Italic(_("— Only in groups")), _("indicates commands available only in groups.")),
                HList(Italic(_("PM-only")), _("lists commands available only in private chat.")),
                HList(Italic(_("Only admins")), _("lists commands that require admin rights.")),
                HList(
                    Italic(Template("({label})", label=_("Toggleable"))),
                    Template(
                        _("means admins can disable or re-enable the command with {disable} and {enable}."),
                        disable=Code("/disable"),
                        enable=Code("/enable"),
                    ),
                ),
            ),
            title=_("/help legend"),
        ),
    )
    return str(doc), buttons.as_markup()
