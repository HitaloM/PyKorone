from __future__ import annotations

from typing import Any

import sentry_sdk

from korone.logger import get_logger

logger = get_logger(__name__)


def _serialize_sentry_extra(value: object) -> str | int | float | bool:
    if isinstance(value, str | int | float | bool):
        return value
    return repr(value)


async def capture_media_exception(
    exception: Exception,
    *,
    stage: str,
    provider: str | None = None,
    source_url: str | None = None,
    extras: dict[str, Any] | None = None,
) -> str | None:
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("module", "medias")
        scope.set_tag("medias.stage", stage)
        if provider:
            scope.set_tag("medias.provider", provider)
        if source_url:
            scope.set_extra("source_url", source_url)
        if extras:
            for key, value in extras.items():
                scope.set_extra(key, _serialize_sentry_extra(value))
        sentry_event_id = sentry_sdk.capture_exception(exception)

    await logger.aerror(
        "[Medias] Exception captured",
        stage=stage,
        provider=provider,
        source_url=source_url,
        error=str(exception),
        sentry_event_id=sentry_event_id,
    )
    return sentry_event_id
