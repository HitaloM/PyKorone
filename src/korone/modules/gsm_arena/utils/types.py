# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from pydantic import BaseModel, Field


class PhoneSearchResult(BaseModel):
    name: str
    url: str

    model_config = {
        "frozen": True,
        "arbitrary_types_allowed": True,
    }


class Phone(BaseModel):
    name: str
    url: str
    picture: str = ""
    specs: dict[str, dict[str, str]] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "arbitrary_types_allowed": True,
    }

    @property
    def status(self) -> str:
        return self._get_spec_value("Launch", "Status")

    @property
    def network(self) -> str:
        return self._get_spec_value("Network", "Technology")

    @property
    def weight(self) -> str:
        return self._get_spec_value("Body", "Weight")

    @property
    def jack(self) -> str:
        return self._get_spec_value("Sound", "3.5mm jack")

    @property
    def usb(self) -> str:
        return self._get_spec_value("Comms", "USB")

    @property
    def sensors(self) -> str:
        return self._get_spec_value("Features", "Sensors")

    @property
    def battery(self) -> str:
        return self._get_spec_value("Battery", "Type")

    @property
    def charging(self) -> str:
        return self._get_spec_value("Battery", "Charging")

    @property
    def display(self) -> str:
        specs = [
            self._get_spec_value("Display", "Type"),
            self._get_spec_value("Display", "Size"),
            self._get_spec_value("Display", "Resolution"),
        ]
        return "\n".join(s for s in specs if s)

    @property
    def chipset(self) -> str:
        specs = [
            self._get_spec_value("Platform", "Chipset"),
            self._get_spec_value("Platform", "CPU"),
            self._get_spec_value("Platform", "GPU"),
        ]
        return "\n".join(s for s in specs if s)

    @property
    def memory(self) -> str:
        return self._get_spec_value("Memory", "Internal")

    @property
    def main_camera(self) -> str:
        return self._get_first_camera_spec("Main Camera")

    @property
    def selfie_camera(self) -> str:
        return self._get_first_camera_spec("Selfie camera")

    def _get_spec_value(self, category: str, attribute: str) -> str:
        return self.specs.get(category, {}).get(attribute, "")

    def _get_first_camera_spec(self, category: str) -> str:
        if category in self.specs:
            camera = next(iter(self.specs[category].items()), (None, None))
            if all(camera):
                return f"{camera[0]} {camera[1]}"
        return ""
