# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import html

from asyncpraw import Reddit
from asyncprawcore import exceptions as redex

from korone.config import REDDIT_ID, REDDIT_SECRET

VALID_ENDS = (
    ".mp4",
    ".jpg",
    ".jpeg",
    "jpe",
    ".png",
    ".gif",
)


REDDIT = Reddit(
    client_id=REDDIT_ID,
    client_secret=REDDIT_SECRET,
    user_agent="PyKorone",
)


async def imagefetcherfallback(subreddit):
    async for post in subreddit.random_rising(limit=10):
        if post.url and post.url.endswith(VALID_ENDS):
            return post


async def titlefetcherfallback(subreddit):
    async for post in subreddit.random_rising(limit=1):
        return post


async def bodyfetcherfallback(subreddit):
    async for post in subreddit.random_rising(limit=10):
        if post.selftext and post.permalink is not post.url:
            return post


async def imagefetcher(c, m, sub: str):
    image_url = False
    subreddit = await REDDIT.subreddit(sub)

    for _ in range(10):
        try:
            post = await subreddit.random() or await imagefetcherfallback(subreddit)

            if post.over_18:
                continue
        except redex.Forbidden:
            await m.reply_text(f"<b>r/{sub}</b> é privado!")
            return
        except (redex.NotFound, KeyError):
            await m.reply_text(f"<b>r/{sub}</b> não existe!")
            return
        except AttributeError:
            continue

        if post.url and post.url.endswith(VALID_ENDS):
            image_url = post.url
            title = post.title
            break

    if not image_url:
        await m.reply_text(f"Não encontrei nenhum conteúdo válido em <b>r/{sub}</b>!")
        return

    keyboard = [[(f"r/{sub}", post.url, "url")]]

    try:
        if post.url.endswith(".mp4"):
            await m.reply_video(image_url, caption=title, reply_markup=c.ikb(keyboard))
        if post.url.endswith((".jpg", ".jpeg", "jpe", ".png")):
            await m.reply_photo(image_url, caption=title, reply_markup=c.ikb(keyboard))
        if post.url.endswith(".gif"):
            await m.reply_animation(
                image_url, caption=title, reply_markup=c.ikb(keyboard)
            )
    except BaseException:
        await m.reply_text(
            f"Falha ao baixar o conteúdo de <b>r/{sub}</b>!\n"
            "Título: <b>{title}</b>\nURL: {image_url}"
        )


async def titlefetcher(c, m, sub: str):
    subreddit = await REDDIT.subreddit(sub)

    try:
        post = await subreddit.random() or await titlefetcherfallback(subreddit)
        post.title
    except redex.Forbidden:
        await m.reply_text(f"<b>r/{sub}</b> é privado!")
        return
    except (redex.NotFound, KeyError):
        await m.reply_text(f"<b>r/{sub}</b> não existe!")
        return
    except AttributeError:
        await m.reply_text(f"Não encontrei nenhum conteúdo válido em <b>r/{sub}</b>!")
        return

    keyboard = c.ikb([[(f"r/{sub}", post.url, "url")]])

    await m.reply_text(post.title, reply_markup=c.ikb(keyboard))


async def bodyfetcher(c, m, sub: str):
    subreddit = await REDDIT.subreddit(sub)

    for _ in range(10):
        try:
            post = await subreddit.random() or await bodyfetcherfallback(subreddit)
            post.title
        except redex.Forbidden:
            await m.reply_text(f"<b>r/{sub}</b> é privado!")
            return
        except (redex.NotFound, KeyError):
            await m.reply_text(f"<b>r/{sub}</b> não existe!")
            return
        except AttributeError:
            continue

        body = None

        if post.selftext and post.permalink is not post.url:
            body = post.selftext
            title = post.title

        if not body:
            continue

        keyboard = [[(f"r/{sub}", post.url, "url")]]

        await m.reply_text(
            f"<b>{title}</b>\n\n{html.escape(body)}",
            reply_markup=c.ikb(keyboard),
            parse_mode="combined",
        )
        return

    await m.reply_text(f"Não encontrei nenhum conteúdo válido em <b>r/{sub}</b>!")
