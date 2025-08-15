from __future__ import annotations

from dataclasses import dataclass

from aiogram.types import Message
from typing import Any
from mistralai import ModerationResponse, ModerationObject

from sophie_bot.modules.ai.utils.new_message_history import NewAIMessageHistory
from sophie_bot.services.ai import mistral_client
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.utils.logger import log

MODERATION_CATEGORIES_TRANSLATES = {
    "sexual": l_(
        "Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness)."
    ),
    "hate_and_discrimination": l_(
        "Content that expresses prejudice, hostility, or advocates discrimination against individuals or groups based on protected characteristics such as race, ethnicity, religion, gender, sexual orientation, or disability."
    ),
    "violence_and_threats": l_(
        "Content that describes, glorifies, incites, or threatens physical violence against individuals or groups."
    ),
    "dangerous_and_criminal_content": l_(
        "Content that promotes or provides instructions for illegal activities or extremely hazardous behaviors that pose a significant risk of physical harm, death, or legal consequences."
    ),
    "selfharm": l_(
        "Content that promotes, instructs, plans, or encourages deliberate self-injury, suicide, eating disorders, or other self-destructive behaviors."
    ),
    "health": l_("Content that contains or tries to elicit detailed or tailored medical advice."),
    "financial": l_("Content that contains or tries to elicit detailed or tailored financial advice."),
    "law": l_("Content that contains or tries to elicit detailed or tailored legal advice."),
    "pii": l_(
        "Content that requests, shares, or attempts to elicit personal identifying information such as full names, addresses, phone numbers, social security numbers, or financial account details."
    ),
}


@dataclass(frozen=True)
class CategoriesDict:
    sexual: bool = False
    hate_and_discrimination: bool = False
    violence_and_threats: bool = False
    dangerous_and_criminal_content: bool = False
    selfharm: bool = False
    health: bool = False
    financial: bool = False
    law: bool = False
    pii: bool = False

    def to_dict(self) -> dict[str, bool]:
        return {
            "sexual": self.sexual,
            "hate_and_discrimination": self.hate_and_discrimination,
            "violence_and_threats": self.violence_and_threats,
            "dangerous_and_criminal_content": self.dangerous_and_criminal_content,
            "selfharm": self.selfharm,
            "health": self.health,
            "financial": self.financial,
            "law": self.law,
            "pii": self.pii,
        }

    @property
    def any_flagged(self) -> bool:
        return any(self.to_dict().values())


@dataclass(frozen=True)
class ModerationResult:
    flagged: bool
    categories: CategoriesDict


async def check_moderator(message: Message) -> ModerationResult:
    history = NewAIMessageHistory()
    await history.add_from_message(message, normalize_texts=True)

    # Use Mistral moderation model; see https://docs.mistral.ai/capabilities/guardrailing/
    # We pass only textual content extracted from the message and history.
    payload: Any = history.to_moderation
    resp: ModerationResponse = await mistral_client.classifiers.moderate_chat_async(
        inputs=payload,
        model="mistral-moderation-latest",
    )
    result: ModerationObject = resp.results[0]

    categories_raw: dict[str, bool] = result.categories or {}
    flagged: bool = any(categories_raw.values())

    log.debug(
        "AI moderation evaluated message",
        flagged=flagged,
        categories=categories_raw,
        input_count=len(history.to_moderation),
    )

    categories = CategoriesDict(
        sexual=categories_raw.get("sexual", False),
        hate_and_discrimination=categories_raw.get("hate_and_discrimination", False),
        violence_and_threats=categories_raw.get("violence_and_threats", False),
        dangerous_and_criminal_content=categories_raw.get("dangerous_and_criminal_content", False),
        selfharm=categories_raw.get("selfharm", False),
        health=categories_raw.get("health", False),
        financial=categories_raw.get("financial", False),
        law=categories_raw.get("law", False),
        pii=categories_raw.get("pii", False),
    )
    return ModerationResult(flagged=flagged, categories=categories)
