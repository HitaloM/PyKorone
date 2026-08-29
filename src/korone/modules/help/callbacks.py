import re
from collections.abc import Mapping

from aiogram import flags
from aiogram.dispatcher.flags import extract_flags_from_object
from aiogram.filters.callback_data import CallbackData

from korone.args import ARGUMENT_HELP_PAYLOAD_KEY, ArgumentSchema

HELP_START_PAYLOAD = "help"
HELP_MODULE_START_PREFIX = "help_module_"
_DEEPLINK_PAYLOAD_MAX_LENGTH = 64
_MODULE_NAME_PATTERN = re.compile(r"[A-Za-z0-9_-]+")


def build_help_module_start_payload(module_name: str) -> str:
    payload = f"{HELP_MODULE_START_PREFIX}{module_name}"
    if not _MODULE_NAME_PATTERN.fullmatch(module_name) or len(payload) > _DEEPLINK_PAYLOAD_MAX_LENGTH:
        msg = "Module name cannot be represented in a Telegram deep-link payload"
        raise ValueError(msg)
    return payload


def parse_help_module_start_payload(payload: str) -> str | None:
    if not payload.startswith(HELP_MODULE_START_PREFIX):
        return None

    module_name = payload.removeprefix(HELP_MODULE_START_PREFIX)
    try:
        expected_payload = build_help_module_start_payload(module_name)
    except ValueError:
        return None
    return module_name if payload == expected_payload else None


def configure_argument_help(handler: object, module_name: str, *, module_public: bool) -> None:
    arguments = getattr(handler, "arguments", None)
    if not isinstance(arguments, ArgumentSchema):
        return

    handler_flags = extract_flags_from_object(handler)
    help_flags = handler_flags.get("help")
    excluded = isinstance(help_flags, Mapping) and bool(help_flags.get("exclude"))
    payload: str | bool = build_help_module_start_payload(module_name) if module_public and not excluded else False
    getattr(flags, ARGUMENT_HELP_PAYLOAD_KEY)(payload)(handler)


class PMHelpModule(CallbackData, prefix="pmhelpmod"):
    module_name: str
    back_to_start: bool = False


class PMHelpModules(CallbackData, prefix="pmhelpback"):
    back_to_start: bool = False
