from typing import TYPE_CHECKING

from stfu_tg import HList, Title

from korone.modules.ai.fsm.pm import AI_GENERATED_TEXT

from .ai_models import AI_MODEL_TO_SHORT_NAME

if TYPE_CHECKING:
    from stfu_tg.doc import Element


def ai_get_model_text(model_name: str) -> str | Element:
    return AI_MODEL_TO_SHORT_NAME.get(model_name, model_name)


def ai_header(*additional_elements: Element) -> Element:
    return HList(Title(AI_GENERATED_TEXT, bold=False), *additional_elements)
