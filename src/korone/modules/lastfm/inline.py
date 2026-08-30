import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, LinkPreviewOptions

from korone.db.repositories.lastfm import LastFMRepository
from korone.logger import get_logger
from korone.modules.metadata import InlineQueryContribution
from korone.ui.rendering import message_text_kwargs
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _

from .callbacks import LastFMMode
from .handlers.base import LastFMHandlerSupport, LastFMUserContext
from .handlers.lfm import LastFMStatusPayload, LastFMStatusView
from .utils import LastFMClient, LastFMError, format_lastfm_error

if TYPE_CHECKING:
    from aiogram.types import InlineQuery

    from korone.ui import MessageContent

    from .utils import LastFMRecentTrack

LASTFM_INLINE_CACHE_SECONDS = 8.0
LASTFM_INLINE_CACHE_MAX_ENTRIES = 1_024

type LastFMInlineCacheKey = tuple[int, str]


@dataclass(frozen=True, slots=True)
class LastFMInlineCacheEntry:
    contribution: InlineQueryContribution
    expires_at: float


_LASTFM_INLINE_CACHE: dict[LastFMInlineCacheKey, LastFMInlineCacheEntry] = {}
_LASTFM_INLINE_INFLIGHT: dict[LastFMInlineCacheKey, asyncio.Task[InlineQueryContribution]] = {}

logger = get_logger(__name__)


def matches_lastfm_inline(query: InlineQuery) -> bool:
    return not query.query.strip()


def _message_content(text: MessageContent, image_url: str | None = None) -> InputTextMessageContent:
    preview_options = None
    if image_url:
        preview_options = LinkPreviewOptions(
            is_disabled=False, url=image_url, prefer_large_media=True, show_above_text=False
        )
    return InputTextMessageContent(**message_text_kwargs(text, link_preview_options=preview_options))


def _article(
    *, result_id: str, title: str, description: str, text: MessageContent, image_url: str | None = None
) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=result_id,
        title=title,
        description=description,
        thumbnail_url=image_url,
        input_message_content=_message_content(text, image_url),
    )


def _informational_contribution(*, title: str, text: str) -> InlineQueryContribution:
    return InlineQueryContribution(
        results=(_article(result_id="information", title=title, description=text, text=text),)
    )


def _track_result(payload: LastFMStatusPayload, track: LastFMRecentTrack) -> InlineQueryResultArticle:
    image_url = LastFMHandlerSupport.resolve_image_url(payload.image_url)
    return _article(
        result_id="track",
        title=_("Current track"),
        description=f"{track.artist} — {track.name}",
        text=payload.text,
        image_url=image_url,
    )


async def _build_lastfm_inline(query: InlineQuery) -> InlineQueryContribution:
    username = await LastFMRepository.get_username(query.from_user.id)
    if not username:
        return _informational_contribution(title=_("Set up Last.fm"), text=LastFMHandlerSupport.missing_username_text())

    user = LastFMUserContext(
        username=username, display_name=query.from_user.first_name, telegram_user_id=query.from_user.id
    )
    client = LastFMClient()
    try:
        recent_tracks = await client.get_recent_tracks(username=username, limit=1)
    except LastFMError as exc:
        return _informational_contribution(title=_("Last.fm unavailable"), text=format_lastfm_error(exc))

    if not recent_tracks:
        return _informational_contribution(title=_("No recent scrobbles"), text=LastFMStatusView.empty_state_text())

    track = recent_tracks[0]
    try:
        status_payload = await LastFMStatusView.build_status_payload_from_tracks(
            user=user, mode=LastFMMode.COMPACT, tracks=recent_tracks
        )
    except LastFMError as exc:
        return _informational_contribution(title=_("Last.fm unavailable"), text=format_lastfm_error(exc))

    if status_payload is not None:
        return InlineQueryContribution(results=(_track_result(status_payload, track),))

    return _informational_contribution(title=_("No recent scrobbles"), text=LastFMStatusView.empty_state_text())


def _prune_lastfm_inline_cache(now: float) -> None:
    expired_keys = [key for key, entry in _LASTFM_INLINE_CACHE.items() if entry.expires_at <= now]
    for key in expired_keys:
        _LASTFM_INLINE_CACHE.pop(key, None)

    overflow = len(_LASTFM_INLINE_CACHE) - LASTFM_INLINE_CACHE_MAX_ENTRIES
    if overflow <= 0:
        return

    oldest_keys = sorted(_LASTFM_INLINE_CACHE, key=lambda key: _LASTFM_INLINE_CACHE[key].expires_at)[:overflow]
    for key in oldest_keys:
        _LASTFM_INLINE_CACHE.pop(key, None)


def _finish_lastfm_inline_load(key: LastFMInlineCacheKey, task: asyncio.Task[InlineQueryContribution]) -> None:
    if _LASTFM_INLINE_INFLIGHT.get(key) is task:
        _LASTFM_INLINE_INFLIGHT.pop(key, None)

    if task.cancelled():
        return

    exception = task.exception()
    if exception is not None:
        return

    loop = task.get_loop()
    now = loop.time()
    _LASTFM_INLINE_CACHE[key] = LastFMInlineCacheEntry(
        contribution=task.result(), expires_at=now + LASTFM_INLINE_CACHE_SECONDS
    )
    _prune_lastfm_inline_cache(now)


async def provide_lastfm_inline(query: InlineQuery) -> InlineQueryContribution:
    loop = asyncio.get_running_loop()
    cache_key = (query.from_user.id, get_i18n().current_locale)
    if cached := _LASTFM_INLINE_CACHE.get(cache_key):
        if cached.expires_at > loop.time():
            await logger.adebug("Last.fm inline cache hit", cache_entry_count=len(_LASTFM_INLINE_CACHE))
            return cached.contribution
        _LASTFM_INLINE_CACHE.pop(cache_key, None)

    await logger.adebug("Last.fm inline cache miss", cache_entry_count=len(_LASTFM_INLINE_CACHE))
    task = _LASTFM_INLINE_INFLIGHT.get(cache_key)
    if task is None:
        task = asyncio.create_task(_build_lastfm_inline(query), name=f"lastfm-inline:{query.from_user.id}")
        _LASTFM_INLINE_INFLIGHT[cache_key] = task
        task.add_done_callback(lambda completed, key=cache_key: _finish_lastfm_inline_load(key, completed))
        await logger.adebug("Last.fm inline load started", inflight_count=len(_LASTFM_INLINE_INFLIGHT))
    else:
        await logger.adebug("Last.fm inline in-flight load joined", inflight_count=len(_LASTFM_INLINE_INFLIGHT))

    # A cancelled waiter must not cancel the shared load needed by other requests or the short-lived cache.
    return await asyncio.shield(task)


async def shutdown_lastfm_inline() -> None:
    tasks = tuple(_LASTFM_INLINE_INFLIGHT.values())
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    _LASTFM_INLINE_INFLIGHT.clear()
    _LASTFM_INLINE_CACHE.clear()
