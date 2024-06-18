from typing import Union

from sophie_bot.config import CACHE_TTL
from sophie_bot.db.models import LanguageModel
from sophie_bot.utils.cached import cached


@cached(ttl=CACHE_TTL.language_ttl)
async def cache_get_locale_name(chat_id: int) -> Union[str, bool]:
    model = await LanguageModel.find_one(LanguageModel.chat_id == chat_id)

    return model.locale_name if model else False
