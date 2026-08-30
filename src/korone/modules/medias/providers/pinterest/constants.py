import re

import aiohttp

PINTEREST_HOST_PATTERN = r"(?:[A-Za-z0-9-]+\.)?pinterest\.(?:com(?:\.[A-Za-z]{2})?|co\.[A-Za-z]{2}|[A-Za-z]{2,3})"

PATTERN = re.compile(
    rf"https?://(?:"
    rf"{PINTEREST_HOST_PATTERN}/pin/(?:[^/\s?#]+--)?\d+/?"
    rf"|{PINTEREST_HOST_PATTERN}/url_shortener/[A-Za-z0-9_-]+/redirect/?"
    rf"|(?:www\.)?pin\.it/[A-Za-z0-9_-]+/?"
    rf")(?:\?[^\s#]*)?(?:#[^\s]*)?",
    re.IGNORECASE,
)

POST_ID_PATTERN = re.compile(r"/pin/(?:[^/\s?#]+--)?(?P<id>\d+)(?:[/?#]|$)", re.IGNORECASE)
URL_SHORTENER_ID_PATTERN = re.compile(r"/url_shortener/(?P<id>[A-Za-z0-9_-]+)/redirect(?:[/?#]|$)", re.IGNORECASE)
RELAY_PAYLOAD_PATTERN = re.compile(
    r'__PWS_RELAY_REGISTER_COMPLETED_REQUEST__\(\s*"[^"]*"\s*,\s*'
    r'(?P<payload>\{"data"\s*:\s*\{.+?\}\})\s*\)\s*;?\s*</script>',
    re.IGNORECASE | re.DOTALL,
)

PIN_PAGE_URL = "https://www.pinterest.com/pin/{post_id}/"
URL_SHORTENER_REDIRECT_URL = "https://api.pinterest.com/url_shortener/{short_id}/redirect/"
PINTEREST_TIMEOUT = aiohttp.ClientTimeout(total=90, connect=20, sock_read=60)
MAX_REDIRECTS = 5
REQUEST_RETRY_ATTEMPTS = 3
REQUEST_RETRY_BASE_DELAY_SECONDS = 0.4
PINTEREST_HLS_TIMEOUT_SECONDS = 180

VIDEO_LIST_KEYS = ("video_list", "videoList")
VIDEO_VARIANT_KEYS = (
    "v_1080p",
    "v1080P",
    "v_720p",
    "v720P",
    "v_480p",
    "v480P",
    "v_360p",
    "v360P",
    "v_240p",
    "v240P",
    "v_exp7",
    "vEXP7",
    "v_exp6",
    "vEXP6",
    "v_exp5",
    "vEXP5",
    "v_exp4",
    "vEXP4",
    "v_exp3",
    "vEXP3",
    "v_exp2",
    "vEXP2",
    "v_exp1",
    "vEXP1",
    "v_exp0",
    "vEXP0",
    "v_hlsv4",
    "vHLSV4",
    "v_hlsv3",
    "vHLSV3",
    "vHLSV3MOBILE",
)
