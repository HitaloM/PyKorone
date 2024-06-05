# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

from korone import app_dir
from korone.modules.lastfm.utils.api import LastFMAlbum, LastFMArtist, LastFMTrack

with Path(app_dir / "resources/misc/everynoise_genres.txt").open(encoding="utf-8") as file:
    ACCEPTABLE_TAGS = {line.strip().lower() for line in file}


def format_tags(item: LastFMTrack | LastFMAlbum | LastFMArtist) -> str:
    tags_text = ""
    if item:
        tags_text = " ".join(
            f"#{
                t.replace("(", "_")
                .replace(")", "_")
                .replace(",", "_")
                .replace('"', "_")
                .replace(".", "_")
                .replace(";", "_")
                .replace(":", "_")
                .replace("'", "_")
                .replace("-", "_")
                .replace(" ", "_")
                .replace("/", "_")
            }"
            for t in (tag.lower() for tag in item.tags or [])
            if any(x in ACCEPTABLE_TAGS for x in t.split(" "))
        )
    return tags_text
