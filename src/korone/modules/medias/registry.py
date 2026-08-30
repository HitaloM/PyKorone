from dataclasses import dataclass

from .models import MediaProvider, MediaRequest
from .urls import normalize_media_url


@dataclass(frozen=True, slots=True)
class ProviderRegistry:
    providers: tuple[MediaProvider, ...]

    def __post_init__(self) -> None:
        keys = [provider.info.key for provider in self.providers]
        if len(keys) != len(set(keys)):
            msg = "Media provider keys must be unique"
            raise ValueError(msg)

    def match(self, text: str) -> MediaRequest | None:
        for provider in self.providers:
            for match in provider.info.pattern.finditer(text):
                if url := normalize_media_url(match.group(0)):
                    return MediaRequest(provider=provider, url=url)
        return None

    def contains(self, provider: MediaProvider) -> bool:
        return any(candidate is provider for candidate in self.providers)
