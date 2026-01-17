from typing import Optional

from ass_tg.entities import ArgEntities
from ass_tg.exceptions import ArgCustomError
from babel.support import LazyProxy

from sophie_bot.modules.notes.utils.buttons_processor.ass_types.SophieButtonABC import AssButtonData, SophieButtonABC
from sophie_bot.utils.i18n import lazy_gettext as l_, gettext as _


class URLButton(SophieButtonABC):
    button_type_names = ("url",)
    ignored_entities = ("url",)

    allowed_protocols = ("http", "https")

    def needed_type(self) -> tuple[LazyProxy, LazyProxy]:
        return l_("URL Button"), l_("URL Buttons")

    def examples(self) -> Optional[dict[str, Optional[LazyProxy]]]:
        return {
            "[Button name](btnurl:https://google.com)": None,
        }

    async def parse(self, text: str, offset: int, entities: ArgEntities) -> tuple[int, AssButtonData[str]]:
        length, data = await super().parse(text, offset, entities)
        raw_url: str = data.arguments[0]

        # Check protocols
        if not any(raw_url.startswith(protocol) for protocol in self.allowed_protocols):
            raise ArgCustomError(
                _("URL must start with http or https"),
                offset=offset + self.data_offset,
                length=len(raw_url),
            )

        return length, data
