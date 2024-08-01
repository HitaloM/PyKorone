# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from pydantic import BaseModel, Field


class Node(BaseModel):
    typename: str | None = Field(alias="__typename", default=None)
    id: str | None = None
    shortcode: str | None = None
    text: str | None = None
    commenter_count: int | None = None
    dimensions: dict | None = None
    display_resources: list[dict] | None = None
    is_video: bool | None = None
    display_url: str | None = None
    video_url: str | None = None


class Edge(BaseModel):
    node: Node | None = None


class EdgeMediaToCaption(BaseModel):
    edges: list[Edge] | None = None


class Owner(BaseModel):
    username: str | None = None


class CoauthorProducers(BaseModel):
    username: str | None = None


class Dimensions(BaseModel):
    height: int | None = None
    width: int | None = None


class DisplayResources(BaseModel):
    config_width: int | None = None
    config_height: int | None = None
    src: str | None = None


class EdgeSidecarToChildren(BaseModel):
    edges: list[Edge] | None = None


class StoriesData(BaseModel):
    url: str | None = None


class ShortcodeMedia(BaseModel):
    typename: str | None = Field(alias="__typename", default=None)
    media_id: str | None = Field(alias="id", default=None)
    shortcode: str | None = None
    dimensions: Dimensions | None = None
    display_resources: list[DisplayResources] | None = None
    is_video: bool | None = None
    title: str | None = None
    video_url: str | None = None
    edge_media_to_caption: EdgeMediaToCaption | None = None
    edge_sidecar_to_children: EdgeSidecarToChildren | None = None
    display_url: str | None = None
    owner: Owner | None = None
    coauthor_producers: list[CoauthorProducers] | None = None


class InstagramDataData(BaseModel):
    xdt_shortcode_media: ShortcodeMedia | None = None


class InstagramData(BaseModel):
    shortcode_media: ShortcodeMedia | None = None
    data: InstagramDataData | None = None
