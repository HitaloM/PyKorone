from typing import Any, Optional

from ass_tg.entities import ArgEntities
from ass_tg.exceptions import ArgTypeError
from ass_tg.types import OrArg
from ass_tg.types.base_abc import ArgFabric

from sophie_bot.modules.notes.utils.buttons_processor.ass_types.SophieButtonABC import AssButtonData
from sophie_bot.modules.notes.utils.buttons_processor.registry import ALL_BUTTONS
from sophie_bot.utils.i18n import lazy_gettext as l_


class ButtonArg(OrArg):
    def __init__(self, description: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(
            *ALL_BUTTONS,
            description=description,
            **kwargs,
        )


class ButtonsArg(ArgFabric[list[AssButtonData]]):
    know_the_end = True
    know_the_start = True

    def __init__(self, description: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(description=description)
        self.child = ButtonArg()

    def needed_type(self):
        return l_("Buttons"), l_("Buttons")

    def get_start(self, raw_text: str, entities: ArgEntities) -> int:
        from sophie_bot.modules.notes.utils.buttons_processor.registry import ALL_BUTTONS

        indices = [i for i, char in enumerate(raw_text) if char == "["]
        for i in indices:
            if self._check_sequence(raw_text[i:], entities, ALL_BUTTONS):
                return i
        return len(raw_text)

    def _check_sequence(self, text: str, entities: ArgEntities, buttons) -> bool:
        offset = 0
        while offset < len(text):
            while offset < len(text) and text[offset].isspace():
                offset += 1

            if offset >= len(text):
                break

            subtext = text[offset:]
            matched = False

            for btn in buttons:
                if btn.check(subtext, entities):
                    try:
                        # get_end returns index relative to subtext
                        end = btn.get_end(subtext, entities)
                        offset += end + 1
                        matched = True
                        break
                    except Exception:
                        continue

            if not matched:
                return False

        return True

    async def parse(self, text: str, offset: int, entities: ArgEntities) -> tuple[int, list[AssButtonData]]:
        results = []
        total_length = 0
        while text.lstrip():
            stripped_text = text.lstrip()
            lstrip_len = len(text) - len(stripped_text)

            total_length += lstrip_len
            offset += lstrip_len
            text = stripped_text

            if not self.child.check(text, entities.cut_before(total_length)):
                break

            try:
                arg = await self.child(text, offset, entities.cut_before(total_length))
                results.append(arg.value)
                total_length += arg.length
                offset += arg.length
                text = text[arg.length :]
            except ArgTypeError:
                break

        if not results:
            return 0, []

        return total_length, results


ButtonsArgList = ButtonsArg
