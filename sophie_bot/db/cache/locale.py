from typing import Union

from sophie_bot.constants import CACHE_LANGUAGE_TTL_SECONDS
from sophie_bot.db.models import LanguageModel
from sophie_bot.utils.cached import cached


@cached(ttl=CACHE_LANGUAGE_TTL_SECONDS)
async def cache_get_locale_name(chat_id: int) -> Union[str, bool]:
    model = await LanguageModel.find_one(LanguageModel.chat_id == chat_id)

    return model.locale_name if model else False
