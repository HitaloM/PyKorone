import asyncio
import logging

import mistralai.httpclient
import mistralai.sdk
import pytest

from sophie_bot.utils.i18n import I18nNew


# Monkey patch mistralai's close_clients to avoid log spam during shutdown
# caused by asyncio.run() creating a new loop and logging "Using selector: EpollSelector"
# when the logging system might be partially closed.
def _safe_close_clients(owner, sync_client, sync_supplied, async_client, async_supplied):
    if sync_client and not sync_supplied:
        sync_client.close()

    if async_client and not async_supplied:
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(async_client.aclose())
            else:
                asyncio.run_coroutine_threadsafe(async_client.aclose(), loop)
        except Exception:
            pass

    owner.client = None
    owner.async_client = None


mistralai.httpclient.close_clients = _safe_close_clients
mistralai.sdk.close_clients = _safe_close_clients


@pytest.fixture(scope="session", autouse=True)
def i18n_context():
    i18n = I18nNew(path="locales")
    from ass_tg.i18n import gettext_ctx

    token = gettext_ctx.set(i18n)

    with i18n.context():
        yield i18n

    gettext_ctx.reset(token)
