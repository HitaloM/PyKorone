from enum import Enum


class OldAIModels(str, Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    O1_MINI = "o1-mini"
    O3 = "o3-mini"
    GPT_5_MINI = "gpt-5-mini"


OLD_DEFAULT_MODEL = OldAIModels.GPT_5_MINI
