from aiogram.types import Message
from openai.types import Moderation

from sophie_bot.modules.ai.utils.message_history import AIMessageHistory
from sophie_bot.services.ai import openai_client
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.utils.logger import log

MODERATION_CATEGORIES_TRANSLATES = {
    "harassment": l_("Content that expresses, incites, or promotes harassing language towards any target."),
    "harassment/threatening": l_("Harassment content that also includes violence or serious harm towards any target."),
    "hate": l_(
        "Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste. Hateful content aimed at non-protected groups (e.g., chess players) is harassment."
    ),
    "hate/threatening": l_(
        "Hateful content that also includes violence or serious harm towards the targeted group based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste."
    ),
    "illicit": l_(
        "Content that includes instructions or advice that facilitate the planning or execution of wrongdoing, or that gives advice or instruction on how to commit illicit acts. For example, 'how to shoplift' would fit this category."
    ),
    "illicit/violent": l_(
        "Content that includes instructions or advice that facilitate the planning or execution of wrongdoing that also includes violence, or that gives advice or instruction on the procurement of any weapon."
    ),
    "self-harm": l_(
        "Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders."
    ),
    "self-harm/instructions": l_(
        "Content that encourages performing acts of self-harm, such as suicide, cutting, and eating disorders, or that gives instructions or advice on how to commit such acts."
    ),
    "self-harm/intent": l_(
        "Content where the speaker expresses that they are engaging or intend to engage in acts of self-harm, such as suicide, cutting, and eating disorders."
    ),
    "sexual": l_(
        "Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness)."
    ),
    "sexual-minors": l_("Sexual content that includes an individual who is under 18 years old."),
    "violence": l_("Content that depicts death, violence, or physical injury."),
    "violence/graphic": l_("Content that depicts death, violence, or physical injury in graphic detail."),
}


async def check_moderator(message: Message) -> Moderation:
    history = AIMessageHistory()
    await history.add_from_message(message)

    results = await openai_client.moderations.create(input=history.to_moderation, model="omni-moderation-latest")
    result = results.results[0]

    log.debug("check_moderator", result=result)
    return result
