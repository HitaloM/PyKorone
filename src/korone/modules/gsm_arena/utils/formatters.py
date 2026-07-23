from typing import TYPE_CHECKING

from aiogram.types import (
    InputMediaPhoto,
    InputRichBlockDetails,
    InputRichBlockPhoto,
    InputRichBlockSectionHeading,
    InputRichBlockTable,
    InputRichBlockUnion,
    InputRichMessage,
    RichBlockCaption,
    RichBlockTableCell,
)
from stfu_tg import Bold, Doc, KeyValue, Section

from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from .types import Phone

from .images import frame_device_image_url

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


def _build_rich_table(rows: SpecRows) -> InputRichBlockTable | None:
    cells: list[list[RichBlockTableCell]] = []

    for label, raw_value in rows:
        value = _normalize_spec_value(raw_value)
        if not value:
            continue

        cells.append([
            RichBlockTableCell(align="left", valign="top", text=str(label), is_header=True),
            RichBlockTableCell(align="left", valign="top", text=value),
        ])

    if not cells:
        return None
    return InputRichBlockTable(cells=cells, is_bordered=True, is_striped=True)


def format_phone_rich(phone: Phone) -> InputRichMessage:
    blocks: list[InputRichBlockUnion] = [InputRichBlockSectionHeading(text=phone.name, size=1)]

    if picture_url := frame_device_image_url(phone.picture):
        blocks.append(
            InputRichBlockPhoto(photo=InputMediaPhoto(media=picture_url), caption=RichBlockCaption(text=phone.name))
        )

    for index, (title, rows) in enumerate(_phone_spec_sections(phone)):
        if (table := _build_rich_table(rows)) is None:
            continue

        blocks.append(InputRichBlockDetails(summary=str(title), blocks=[table], is_open=index == 0))

    return InputRichMessage(blocks=blocks)
