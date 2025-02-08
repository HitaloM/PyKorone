from enum import Enum


class Models(str, Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    O1_MINI = "o1-mini"
    O3 = "o3-mini"


DEFAULT_MODEL = Models.GPT_4O_MINI


MODEL_TITLES: dict[Models, str] = {
    Models.GPT_4O_MINI: "4o-",
    Models.GPT_4O: "4o",
    Models.O1_MINI: "o1-",
    Models.O3: "o3-",
}
