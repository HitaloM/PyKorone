import pytest

from sophie_bot.utils.i18n import I18nNew


@pytest.fixture(scope="session", autouse=True)
def i18n_context():
    i18n = I18nNew(path="locales")
    from ass_tg.i18n import gettext_ctx
    token = gettext_ctx.set(i18n)

    with i18n.context():
        yield i18n

    gettext_ctx.reset(token)
