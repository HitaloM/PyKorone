# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pydantic import BaseModel, Field


class User(BaseModel):
    username: str


class ImageCandidate(BaseModel):
    url: str
    height: int
    width: int


class ImageVersions(BaseModel):
    candidates: list[ImageCandidate]


class VideoVersions(BaseModel):
    url: str


class LinkPreviewAttachment(BaseModel):
    display_url: str
    image_url: str
    title: str
    url: str


class TextPostAppInfo(BaseModel):
    link_preview_attachment: LinkPreviewAttachment | None = None


class CarouselMedia(BaseModel):
    original_height: int
    original_width: int
    image_versions2: ImageVersions | None = None
    video_versions: list[VideoVersions] | None = None


class Caption(BaseModel):
    text: str


class Post(BaseModel):
    user: User
    post_id: str = Field(alias="id")
    text_post_app_info: TextPostAppInfo | None = None
    code: str
    carousel_media: list[CarouselMedia] | None = None
    image_versions2: ImageVersions | None = None
    original_height: int | None = 0
    original_width: int | None = 0
    video_versions: list[VideoVersions] | None = None
    caption: Caption | None = None


class ThreadItem(BaseModel):
    post: Post
    line_type: str
    should_show_replies_cta: bool


class ThreadsDataNode(BaseModel):
    thread_items: list[ThreadItem]


class ThreadsDataEdge(BaseModel):
    node: ThreadsDataNode


class ThreadsDataDataData(BaseModel):
    edges: list[ThreadsDataEdge]


class ThreadsDataData(BaseModel):
    data: ThreadsDataDataData


class ThreadsData(BaseModel):
    data: ThreadsDataData
