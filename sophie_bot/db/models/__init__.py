from typing import List, Type

from beanie import Document

from sophie_bot.db.models.ai_autotranslate import AIAutotranslateModel
from sophie_bot.db.models.ai_enabled import AIEnabledModel
from sophie_bot.db.models.ai_memory import AIMemoryModel
from sophie_bot.db.models.ai_moderator import AIModeratorModel
from sophie_bot.db.models.ai_provider import AIProviderModel
from sophie_bot.db.models.ai_usage import AIUsageModel
from sophie_bot.db.models.antiflood import AntifloodModel
from sophie_bot.db.models.api_token import ApiTokenModel
from sophie_bot.db.models.beta import BetaModeModel
from sophie_bot.db.models.chat import ChatModel, ChatTopicModel, UserInGroupModel
from sophie_bot.db.models.chat_admin import ChatAdminModel
from sophie_bot.db.models.chat_connections import ChatConnectionModel
from sophie_bot.db.models.chat_photo import ChatPhotoModel
from sophie_bot.db.models.disabling import DisablingModel
from sophie_bot.db.models.federations import Federation, FederationBan
from sophie_bot.db.models.filters import FiltersModel
from sophie_bot.db.models.greetings import GreetingsModel
from sophie_bot.db.models.language import LanguageModel
from sophie_bot.db.models.notes import NoteModel
from sophie_bot.db.models.privatenotes import PrivateNotesModel
from sophie_bot.db.models.refresh_token import RefreshTokenModel
from sophie_bot.db.models.rules import RulesModel
from sophie_bot.db.models.settings_keyvalue import GlobalSettings
from sophie_bot.db.models.ws_user import WSUserModel

models: List[Type[Document]] = [
    ChatModel,
    ChatPhotoModel,
    UserInGroupModel,
    ChatTopicModel,
    ChatAdminModel,
    LanguageModel,
    ChatConnectionModel,
    NoteModel,
    BetaModeModel,
    GlobalSettings,
    AIEnabledModel,
    AIUsageModel,
    AIAutotranslateModel,
    AIModeratorModel,
    AIMemoryModel,
    DisablingModel,
    PrivateNotesModel,
    RulesModel,
    GreetingsModel,
    WSUserModel,
    FiltersModel,
    AIProviderModel,
    AntifloodModel,
    ApiTokenModel,
    Federation,
    FederationBan,
    RefreshTokenModel
]
