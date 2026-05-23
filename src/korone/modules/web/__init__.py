from aiogram import Router
from stfu_tg import Doc

from korone.modules.metadata import ModuleManifest, ModulePackage
from korone.utils.i18n import LazyProxy
from korone.utils.i18n import lazy_gettext as l_

from .callbacks import GetIPCallback as GetIPCallback
from .handlers.ip import IPInfoCallbackHandler, IPInfoHandler
from .handlers.url import URLNormalizeHandler
from .handlers.whois import WhoisHandler

router = Router(name="web")

manifest = ModuleManifest(
    package=ModulePackage(
        name=l_("Web"),
        icon="🌐",
        summary=l_("IP, WHOIS, and URL utilities"),
        description=LazyProxy(lambda: Doc(l_("Look up IP/domain details, query WHOIS records, and normalize URLs."))),
    ),
    router=router,
    handlers=(IPInfoHandler, IPInfoCallbackHandler, WhoisHandler, URLNormalizeHandler),
)
