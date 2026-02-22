from sentry_sdk import capture_exception


def capture_sentry(exception: Exception) -> str | None:
    return capture_exception(exception)
