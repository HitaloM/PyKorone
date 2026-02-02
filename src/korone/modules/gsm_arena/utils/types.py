from dataclasses import dataclass, field
from itertools import starmap

type Specs = dict[str, dict[str, str]]


@dataclass(frozen=True, slots=True)
class PhoneSearchResult:
    name: str
    url: str


@dataclass(frozen=True, slots=True)
class Phone:
    name: str
    url: str
    picture: str = ""
    specs: Specs = field(default_factory=dict)

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
        return self._join_specs(("Display", "Type"), ("Display", "Size"), ("Display", "Resolution"))

    @property
    def chipset(self) -> str:
        return self._join_specs(("Platform", "Chipset"), ("Platform", "CPU"), ("Platform", "GPU"))

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

    def _join_specs(self, *pairs: tuple[str, str]) -> str:
        values = list(starmap(self._get_spec_value, pairs))
        return "\n".join(value for value in values if value)

    def _get_first_camera_spec(self, category: str) -> str:
        camera_items = self.specs.get(category, {}).items()
        if camera_spec := next(iter(camera_items), (None, None)):
            return f"{camera_spec[0]} {camera_spec[1]}" if all(camera_spec) else ""
        return ""
