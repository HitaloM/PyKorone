from html import escape
from typing import TYPE_CHECKING

from stfu_tg import Bold, Doc, KeyValue, Section

from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from .types import Phone

type SpecRows = tuple[tuple[str, str], ...]
type SpecSections = tuple[tuple[str, SpecRows], ...]


def _normalize_spec_value(value: str) -> str:
    parts = [part.strip() for part in value.splitlines() if part.strip() and part.strip() != "-"]
    return "; ".join(parts)


def _build_section_items(attributes: SpecRows) -> list[KeyValue]:
    values: list[KeyValue] = []

    for key, raw_value in attributes:
        normalized = _normalize_spec_value(raw_value)
        if normalized:
            values.append(KeyValue(key, normalized))

    return values


def _phone_spec_sections(phone: Phone) -> SpecSections:
    return (
        (
            _("Overview"),
            (
                (_("Announced"), phone.spec("Launch", "Announced")),
                (_("Status"), phone.status),
                (_("Network"), phone.network),
                (_("Operating system"), phone.spec("Platform", "OS")),
                (_("Dimensions"), phone.spec("Body", "Dimensions")),
                (_("Weight"), phone.weight),
                (_("Build"), phone.spec("Body", "Build")),
                (_("SIM"), phone.spec("Body", "SIM")),
            ),
        ),
        (
            _("Display and Hardware"),
            (
                (_("Display"), phone.display),
                (_("Protection"), phone.spec("Display", "Protection")),
                (_("Chipset"), phone.spec("Platform", "Chipset")),
                (_("Processor"), phone.spec("Platform", "CPU")),
                (_("Graphics"), phone.spec("Platform", "GPU")),
                (_("Memory"), phone.memory),
                (_("Card slot"), phone.spec("Memory", "Card slot")),
            ),
        ),
        (
            _("Cameras"),
            (
                (_("Rear Camera"), phone.main_camera),
                (_("Features"), phone.spec("Main Camera", "Features")),
                (_("Rear Camera Video"), phone.spec("Main Camera", "Video")),
                (_("Front Camera"), phone.selfie_camera),
                (_("Front Camera Video"), phone.spec("Selfie camera", "Video")),
            ),
        ),
        (
            _("Connectivity"),
            (
                (_("WLAN"), phone.spec("Comms", "WLAN")),
                (_("Bluetooth"), phone.spec("Comms", "Bluetooth")),
                (_("Positioning"), phone.spec("Comms", "Positioning")),
                (_("NFC"), phone.spec("Comms", "NFC")),
                (_("3.5mm jack"), phone.jack),
                (_("USB"), phone.usb),
                (_("Sensors"), phone.sensors),
            ),
        ),
        (
            _("Battery and Other"),
            (
                (_("Battery"), phone.battery),
                (_("Charging"), phone.charging),
                (_("Colors"), phone.spec("Misc", "Colors")),
                (_("Models"), phone.spec("Misc", "Models")),
                (_("Price"), phone.spec("Misc", "Price")),
            ),
        ),
    )


def format_phone(phone: Phone) -> str:
    doc = Doc(Bold(phone.name))

    for title, rows in _phone_spec_sections(phone):
        items = _build_section_items(rows)
        if not items:
            continue

        doc += ""
        doc += Section(title=title)
        doc += ""

        for index, item in enumerate(items):
            doc += item
            if index < len(items) - 1:
                doc += ""

    return str(doc)


def format_phone_rich(phone: Phone) -> str:
    blocks = [f"<h1>{escape(phone.name)}</h1>"]

    if phone.picture:
        blocks.append(
            f'<figure><img src="{escape(phone.picture, quote=True)}"/>'
            f"<figcaption>{escape(phone.name)}</figcaption></figure>"
        )

    for index, (title, rows) in enumerate(_phone_spec_sections(phone)):
        normalized_rows = [(label, normalized) for label, value in rows if (normalized := _normalize_spec_value(value))]
        if not normalized_rows:
            continue

        table_rows = "".join(
            f"<tr><th>{escape(str(label))}</th><td>{escape(value)}</td></tr>" for label, value in normalized_rows
        )
        open_attribute = " open" if index == 0 else ""
        blocks.append(
            f"<details{open_attribute}><summary>{escape(str(title))}</summary>"
            f"<table bordered striped>{table_rows}</table></details>"
        )

    return "".join(blocks)
