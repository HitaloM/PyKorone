from typing import Optional
from sentry_sdk import capture_exception


def capture_sentry(exception: Exception) -> Optional[str]:
    return capture_exception(exception)
