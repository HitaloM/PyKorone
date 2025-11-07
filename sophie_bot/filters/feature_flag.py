from aiogram.filters import BaseFilter
from aiogram.types import Message

from sophie_bot.utils.feature_flags import is_enabled


class FeatureFlagFilter(BaseFilter):
    """Filter that checks if a feature flag is enabled."""

    def __init__(self, feature: str, enabled: bool = True):
        """
        Initialize the feature flag filter.

        Args:
            feature: The feature flag to check (must be a valid FeatureType)
            enabled: If True, handler is enabled when flag is True
                    If False, handler is enabled when flag is False (reverse logic)
        """
        self.feature = feature  # type: ignore
        self.enabled = enabled

    async def __call__(self, message: Message) -> bool:
        """Check if the feature flag condition is met."""
        flag_enabled = await is_enabled(self.feature)  # type: ignore
        return flag_enabled == self.enabled
