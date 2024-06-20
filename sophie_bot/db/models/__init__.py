from sophie_bot.db.models.beta import BetaModeModel
from sophie_bot.db.models.chat import ChatModel, UserInGroupModel, ChatTopicModel
from sophie_bot.db.models.chat_connections import ChatConnectionModel
from sophie_bot.db.models.language import LanguageModel

models = [
    BetaModeModel,
    ChatModel,
    UserInGroupModel,
    ChatTopicModel,
    LanguageModel,
    ChatConnectionModel
]
