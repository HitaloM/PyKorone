MODEL_NAME = "gpt-4o-mini"
MODEL_SHORT_NAME = "GPT-4o mini"

AI_MODEL_TO_SHORT_NAME = {MODEL_NAME: MODEL_SHORT_NAME}


def get_openai_model_name() -> str:
    return MODEL_NAME
