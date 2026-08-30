import re

INSTAGRAM_HOST = "instagram.com"
INSTAFIX_HOST = "instagram7.com"

PATTERN = re.compile(
    r"https?://(?:www\.)?(?:instagram\.com|instagram7\.com)/(?:reel(?:s?)|p|tv)/[A-Za-z0-9_-]+(?:/[\w-]+)?(?:\?[^\s]+)?",
    re.IGNORECASE,
)
POST_PATTERN = re.compile(r"(?:reel(?:s?)|p|tv)/(?P<post_id>[A-Za-z0-9_-]+)", re.IGNORECASE)
