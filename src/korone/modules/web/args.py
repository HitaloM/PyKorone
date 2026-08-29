from dataclasses import dataclass
from typing import override

from korone.args import ArgumentDescription, ArgumentExamples, ArgumentValueError, TextArg, TransformArg, WordArg
from korone.modules.web.utils.ip import get_ips_from_string
from korone.modules.web.utils.misc import normalize_url
from korone.modules.web.utils.whois import normalize_domain
from korone.ui import Code, template
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_


class DomainArg(TransformArg[str, str]):
    def __init__(self, description: ArgumentDescription | None = None) -> None:
        super().__init__(WordArg(description))

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("Domain name"), l_("Domain names")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {"example.com": None}

    @override
    async def transform(self, value: str) -> str:
        domain = normalize_domain(value)
        if domain is None:
            raise ArgumentValueError(_("A valid domain name is required."))
        return domain


class IPAddressOrDomainArg(TransformArg[str, tuple[str, ...]]):
    def __init__(self, description: ArgumentDescription | None = None) -> None:
        super().__init__(TextArg(description))

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("IP address or domain"), l_("IP addresses or domains")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {"1.1.1.1": l_("IP address"), "example.com": l_("Domain name")}

    @override
    async def transform(self, value: str) -> tuple[str, ...]:
        addresses = await get_ips_from_string(value)
        if not addresses:
            raise ArgumentValueError(_("No valid IP addresses or domains found in the provided input."))
        return tuple(addresses)


@dataclass(frozen=True, slots=True)
class NormalizedURL:
    original: str
    normalized: str


class URLArg(TransformArg[str, NormalizedURL]):
    def __init__(self, description: ArgumentDescription | None = None) -> None:
        super().__init__(TextArg(description))

    @override
    def needed_type(self) -> tuple[ArgumentDescription, ArgumentDescription]:
        return l_("URL"), l_("URLs")

    @property
    @override
    def examples(self) -> ArgumentExamples:
        return {"example.com/path?utm_source=test#section": None}

    @override
    async def transform(self, value: str) -> NormalizedURL:
        normalized = normalize_url(value)
        if normalized is None:
            raise ArgumentValueError(template(_("I couldn't normalize this URL: {url}"), url=Code(value)))
        return NormalizedURL(original=value, normalized=normalized)
