from aiogram import Router
from stfu_tg import Doc

from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .callbacks import GetIPCallback as GetIPCallback
from .handlers.ip import IPInfoCallbackHandler, IPInfoHandler
from .handlers.url import URLNormalizeHandler
from .handlers.whois import WhoisHandler

router = Router(name="web")

__module_name__ = l_("Web")
__module_emoji__ = "🌐"
__module_description__ = l_("IP, WHOIS, and URL utilities")
__module_info__ = LazyProxy(lambda: Doc(l_("Look up IP/domain details, query WHOIS records, and normalize URLs.")))

__handlers__ = (IPInfoHandler, IPInfoCallbackHandler, WhoisHandler, URLNormalizeHandler)
