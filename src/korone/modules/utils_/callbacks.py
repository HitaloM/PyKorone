from aiogram.filters.callback_data import CallbackData


class GoToStartCallback(CallbackData, prefix="go_to_start"):
    pass


class CancelActionCallback(CallbackData, prefix="cancel_action"):
    pass


class LanguageButtonCallback(CallbackData, prefix="lang_btn"):
    pass
