from sophie_bot.modules.ai.fsm.pm import AI_GENERATED_TEXT


def is_ai_message(text: str) -> bool:
    return text.removeprefix("[").startswith(str(AI_GENERATED_TEXT))


def cut_titlebar(text: str) -> str:
    return text.split("\n")[1]
