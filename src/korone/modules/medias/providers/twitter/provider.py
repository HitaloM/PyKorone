from typing import TYPE_CHECKING
from urllib.parse import quote

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.logger import get_logger
from korone.modules.medias.download import DownloadOptions
from korone.modules.medias.models import MediaPost, ProviderInfo

from . import parser
from .constants import FXTWITTER_STATUS_API, PATTERN

if TYPE_CHECKING:
    from typing import Any

    from korone.modules.medias.download import MediaDownloader

    from .client import TwitterClient

logger = get_logger(__name__)


class TwitterProvider:
    info = ProviderInfo(key="twitter", name="Twitter", website="Twitter", pattern=PATTERN)

    def __init__(self, client: TwitterClient, downloader: MediaDownloader) -> None:
        self._client = client
        self._downloader = downloader

    async def fetch(self, url: str) -> MediaPost | None:
        status_id, handle = parser.extract_status_id_and_handle(url)
        if not status_id or not (tweet := await self._fetch_tweet(status_id)):
            return None

        author_name, author_handle = parser.extract_author(tweet)
        if handle and not author_handle:
            author_handle = handle

        quote_payload = parser.extract_quote(tweet)
        quote_text, quote_author_name, quote_author_handle = quote_payload or (None, None, None)
        media = await self._downloader.download(
            parser.extract_media_sources(tweet, max_size=TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES),
            options=DownloadOptions(filename_prefix="x_media", label="FXTwitter"),
        )
        if not media:
            return None

        return MediaPost(
            author_name=author_name or author_handle or "",
            author_handle=author_handle or "",
            text=parser.extract_text(tweet),
            url=parser.extract_post_url(tweet, status_id, author_handle, url),
            website=self.info.website,
            media=media,
            quote_text=quote_text,
            quote_author_name=quote_author_name,
            quote_author_handle=quote_author_handle,
        )

    async def _fetch_tweet(self, status_id: str) -> dict[str, Any] | None:
        endpoint = FXTWITTER_STATUS_API.format(status_id=quote(status_id))
        payload = await self._client.fetch_json(endpoint)
        if not payload:
            return None
        if tweet := parser.extract_tweet_payload(payload):
            return tweet
        await logger.adebug(
            "[FXTwitter] Missing tweet payload",
            status_code=parser.extract_status_code(payload),
            status_message=parser.extract_status_message(payload),
            endpoint=endpoint,
        )
        return None
