# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

from asyncpraw import Reddit

from ..config import config

REDDIT = Reddit(
    client_id=config.get_config("reddit_id"),
    client_secret=config.get_config("reddit_secret"),
    user_agent="linux:com.korone.bot:v1.0.0 (by /u/LordHitsuki)",  # Following Reddit Rules
)


async def imagefetcherfallback(subreddit):
    async for post in subreddit.random_rising(limit=10):
        if post.url and post.url.endswith(
            (".mp4", ".jpg", ".jpeg", "jpe", ".png", ".gif")
        ):
            return post


async def titlefetcherfallback(subreddit):
    async for post in subreddit.random_rising(limit=1):
        return post


async def bodyfetcherfallback(subreddit):
    async for post in subreddit.random_rising(limit=10):
        if post.selftext and post.permalink is not post.url:
            return post
