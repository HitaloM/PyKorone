# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team

from yt_dlp import YoutubeDL

from korone.utils import aiowrap


@aiowrap
def extract_info(instance: YoutubeDL, url: str, download=True):
    return instance.extract_info(url, download)