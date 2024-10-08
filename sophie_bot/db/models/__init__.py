from typing import List, Type

from beanie import Document

from sophie_bot.db.models.ai_autotranslate import AIAutotranslateModel
from sophie_bot.db.models.ai_enabled import AIEnabledModel
from sophie_bot.db.models.ai_usage import AIUsageModel
from sophie_bot.db.models.beta import BetaModeModel
from sophie_bot.db.models.chat import ChatModel, ChatTopicModel, UserInGroupModel
from sophie_bot.db.models.chat_connections import ChatConnectionModel
from sophie_bot.db.models.language import LanguageModel
from sophie_bot.db.models.notes import NoteModel
from sophie_bot.db.models.settings_keyvalue import GlobalSettings

models: List[Type[Document]] = [
    ChatModel,
    UserInGroupModel,
    ChatTopicModel,
    LanguageModel,
    ChatConnectionModel,
    NoteModel,
    BetaModeModel,
    GlobalSettings,
    AIEnabledModel,
    AIUsageModel,
    AIAutotranslateModel,
]
