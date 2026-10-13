import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from korone import aredis, bot
from korone.config import CONFIG
from korone.constants import TELEGRAM_LOCAL_MAX_FILE_SIZE_BYTES, TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.http import HttpClient, http_client

from .cache import MediaCache
from .delivery import TelegramMediaDelivery
from .download import MediaDownloader
from .providers.bluesky import BlueskyClient, BlueskyProvider
from .providers.instagram import InstagramClient, InstagramProvider
from .providers.pinterest import PinterestClient, PinterestProvider
from .providers.reddit import RedditClient, RedditProvider
from .providers.tiktok import TikTokClient, TikTokProvider
from .providers.twitter import TwitterClient, TwitterProvider
from .registry import ProviderRegistry
from .service import MediaService
from .transforms import FFmpegTranscoder, PhotoProcessor

if TYPE_CHECKING:
    from aiogram.types import Message
    from redis.asyncio import Redis

    from .models import MediaProvider


@dataclass(frozen=True, slots=True)
class MediaContainer:
    registry: ProviderRegistry
    service: MediaService
    photos: PhotoProcessor

    def delivery_for(self, message: Message, provider: MediaProvider) -> TelegramMediaDelivery:
        return TelegramMediaDelivery(message, provider.info, self.photos)


def build_media_container(
    *,
    http: HttpClient,
    redis: Redis,
    max_concurrent_downloads: int,
    max_concurrent_transforms: int,
    max_concurrent_posts: int,
) -> MediaContainer:
    cache = MediaCache(redis)
    download_slots = asyncio.Semaphore(max_concurrent_downloads)
    transform_slots = asyncio.Semaphore(max_concurrent_transforms)
    downloader = MediaDownloader(
        http,
        cache,
        download_slots,
        max_size=TELEGRAM_LOCAL_MAX_FILE_SIZE_BYTES if bot.session.api.is_local else TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES,
        local_timeout_seconds=CONFIG.media_local_download_timeout_seconds if bot.session.api.is_local else None,
    )
    photos = PhotoProcessor(transform_slots)
    transcoder = FFmpegTranscoder(transform_slots)

    providers: tuple[MediaProvider, ...] = (
        TwitterProvider(TwitterClient(http), downloader),
        BlueskyProvider(BlueskyClient(http), downloader),
        InstagramProvider(InstagramClient(http), downloader),
        PinterestProvider(PinterestClient(http), downloader, transcoder),
        RedditProvider(RedditClient(http), downloader, transcoder),
        TikTokProvider(TikTokClient(http), downloader),
    )
    registry = ProviderRegistry(providers)
    return MediaContainer(
        registry=registry, service=MediaService(cache, asyncio.Semaphore(max_concurrent_posts)), photos=photos
    )


media_container = build_media_container(
    http=http_client,
    redis=aredis,
    max_concurrent_downloads=CONFIG.media_max_concurrent_downloads,
    max_concurrent_transforms=CONFIG.media_max_concurrent_transforms,
    max_concurrent_posts=CONFIG.media_max_concurrent_posts,
)
