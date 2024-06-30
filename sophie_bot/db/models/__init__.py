from sophie_bot.db.models.beta import BetaModeModel
from sophie_bot.db.models.chat import ChatModel, ChatTopicModel, UserInGroupModel
from sophie_bot.db.models.chat_connections import ChatConnectionModel
from sophie_bot.db.models.language import LanguageModel
from sophie_bot.db.models.notes import NoteModel

models = [BetaModeModel, ChatModel, UserInGroupModel, ChatTopicModel, LanguageModel, ChatConnectionModel, NoteModel]
