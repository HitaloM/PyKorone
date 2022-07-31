# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import pytomlpp
from asyncpraw import Reddit

config_toml = pytomlpp.loads(open("config.toml", "r").read())


REDDIT = Reddit(
    client_id=config_toml["korone"]["reddit_id"],
    client_secret=config_toml["korone"]["reddit_secret"],
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
