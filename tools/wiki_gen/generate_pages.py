from pathlib import Path
from typing import Sequence

from stfu_tg import BlockQuote, Doc, HList, Italic, Template, Title, Url
from stfu_tg.doc import Element
from stfu_tg.md.table import TableMD

from sophie_bot.modules.help.utils.extract_info import (
    HELP_MODULES,
    HandlerHelp,
    ModuleHelp,
    get_aliased_cmds,
)
from sophie_bot.modules.help.utils.format_help import format_cmd, group_handlers
from sophie_bot.services.i18n import i18n
from sophie_bot.utils.i18n import LazyProxy
from sophie_bot.utils.logger import log

wiki_modules = Path("./wiki/docs/modules")
human_pages = Path("./docs/modules")


class ModuleWikiPage:
    # TODO: Use this for /help as well
    __slots__ = ('name', 'module',)

    def __init__(self, name: str, module: ModuleHelp):
        self.name = name
        self.module = module

    @staticmethod
    def _table_row(handler: HandlerHelp) -> tuple[Element, LazyProxy | str, Element]:
        remarks = HList(divider=', ')

        if handler.only_chats:
            remarks.append(Italic('Only in groups'))

        if handler.disableable:
            remarks.append(Italic('Disable-able'))

        return (
            HList(*(format_cmd(cmd) for cmd in handler.cmds)),
            handler.description or "-",
            remarks,
        )

    def _table(self, handlers: Sequence[HandlerHelp]):
        return TableMD(
            ('Commands', 'Description', 'Remarks'),
            *(self._table_row(handler) for handler in handlers)
        )

    def _generate_module_info(self) -> str:
        with i18n.context(), i18n.use_locale('en_US'):
            doc = Doc(
                Title(f'{self.module.name} {self.module.icon}', level=1),
                Title(self.module.description, level=3) if self.module.description else None,
                BlockQuote(self.module.info) if self.module.info else None,

                # Commands groups
                Title('Available commands', level=2),
                *(Title(title, level=3) + self._table(handlers) for title, handlers in group_handlers(self.module.handlers)),

                # Aliased commands
                *(
                    Title(Template('Aliased commands from {module}', module=Url(
                        f"{HELP_MODULES[mod_name].icon} {HELP_MODULES[mod_name].name}",
                        f'/modules/{mod_name}'
                    )), level=3) + self._table(handlers) for mod_name, handlers in get_aliased_cmds(self.name).items()
                )

            )

            return doc.to_md()

    @property
    def is_excluded(self) -> bool:
        return self.module.exclude_public

    @property
    def page(self) -> str:
        text = self._generate_module_info()
        if (human := human_pages / f"{self.name}.md").exists():
            log.debug("- Appending human-maintained page")
            with human.open("r", encoding="utf-8") as f:
                text += "\n---\n" + f.read()

        return text


async def generate_wiki_pages():
    log.warn("Generating wiki documentation...")

    if not wiki_modules.exists():
        wiki_modules.mkdir()

    # Cleanup the modules directory
    for f in wiki_modules.rglob("*"):
        f.unlink()
    wiki_modules.rmdir()

    # Create the modules directory
    wiki_modules.mkdir()

    # Generate wiki pages for each module
    for module_name, module_help in HELP_MODULES.items():
        page = ModuleWikiPage(module_name, module_help)

        if page.is_excluded:
            log.debug(f"Module {module_name} is excluded from the help, skipping")
            continue

        # Generate the module's README.md file
        module_index = wiki_modules / f"{module_name}.md"
        module_index.touch()
        readme_file = module_index.open("w", encoding="utf-8")
        readme_file.write(page.page)

        readme_file.close()

    log.warn('Generating wiki documentation done!')
