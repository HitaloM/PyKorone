from sophie_bot.config import CONFIG
from sophie_bot.utils.i18n import I18nNew

i18n = I18nNew(path="locales", domain="sophie", default_locale=CONFIG.default_locale)
i18n.set_current(i18n)
