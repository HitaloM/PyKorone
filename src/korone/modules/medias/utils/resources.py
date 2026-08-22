import asyncio

from korone.config import CONFIG

MEDIA_DOWNLOAD_SLOTS = asyncio.Semaphore(CONFIG.media_max_concurrent_downloads)
MEDIA_TRANSFORM_SLOTS = asyncio.Semaphore(CONFIG.media_max_concurrent_transforms)
