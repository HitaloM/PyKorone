from __future__ import annotations

import re

FXTWITTER_STATUS_API = "https://api.fxtwitter.com/status/{status_id}"
FXTWITTER_STATUS_API_WITH_HANDLE = "https://api.fxtwitter.com/{handle}/status/{status_id}"
TWITTER_STATUS_API = "https://twitter.com/i/api/graphql/2ICDjqPd81tulZcYrtpTuQ/TweetResultByRestId"
TWITTER_GUEST_TOKEN_API = "https://api.twitter.com/1.1/guest/activate.json"
TWITTER_BEARER_TOKEN = (
    "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)
TWITTER_GUEST_TOKEN_TTL_SECONDS = 3 * 60 * 60

TWITTER_API_BASE_HEADERS = {
    "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
    "x-twitter-client-language": "en",
    "x-twitter-active-user": "yes",
    "content-type": "application/json",
}

TWITTER_STATUS_VARIABLES = {"includePromotedContent": False, "withCommunity": False, "withVoice": False}

TWITTER_STATUS_FEATURES = {
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "tweetypie_unmention_optimization_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": False,
    "tweet_awards_web_tipping_enabled": False,
    "responsive_web_home_pinned_timelines_enabled": True,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "responsive_web_media_download_video_enabled": False,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
}

TWITTER_STATUS_FIELD_TOGGLES = {"withArticleRichContentState": True}

PATTERN = re.compile(
    r"https?://(?:www\.)?(?:x\.com|(?:www\.|mobile\.)?twitter\.com)/"
    r"(?:i/(?:web/)?|[A-Za-z0-9_]{1,15}/)?status/\d+"
    r"(?:/[^\s?#]+)?(?:\?[^\s#]*)?(?:#[^\s]*)?",
    re.IGNORECASE,
)
