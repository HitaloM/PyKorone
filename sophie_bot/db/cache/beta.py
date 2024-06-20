from sophie_bot.config import CACHE_TTL
from sophie_bot.db.models import BetaModeModel, LanguageModel
from sophie_bot.utils.cached import cached


@cached(ttl=CACHE_TTL.default_ttl)
async def cache_get_chat_beta(chat_id: int) -> bool:
    model = await BetaModeModel.find_one(LanguageModel.chat_id == chat_id)

    return bool(model)
