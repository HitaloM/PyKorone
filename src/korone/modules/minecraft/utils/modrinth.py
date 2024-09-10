# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from datetime import timedelta
from enum import StrEnum

import httpx
from cashews import NOT_NONE

from korone.utils.caching import cache

API_BASE_URL = "https://api.modrinth.com/v2"


class HashMethods(StrEnum):
    SHA1 = "sha1"
    SHA512 = "sha512"


class ProjectType(StrEnum):
    MOD = "mod"
    MODPACK = "modpack"
    RESOURCEPACK = "resourcepack"
    SHADER = "shader"


class ModrinthProject:
    def __init__(self, project: str, data: dict) -> None:
        self.url = f"{API_BASE_URL}/project/{project}"
        self.id = data["id"]
        self.slug = data["slug"]
        self.project_type = ProjectType(data["project_type"])
        self.team = data["team"]
        self.name = data["title"]
        self.description = data["description"]
        self.body = data["body"]
        self.body_url = data["body_url"]
        self.published = data["published"]
        self.updated = data["updated"]
        self.status = data["status"]
        self.moderator_message = data.get("moderator_message")
        self.license = data["license"]
        self.client_side = data["client_side"]
        self.server_side = data["server_side"]
        self.downloads = data["downloads"]
        self.followers = data["followers"]
        self.loaders = data["loaders"]
        self.categories = data["categories"]
        self.versions = data["versions"]
        self.icon_url = data["icon_url"]
        self.issues_url = data.get("issues_url", "")
        self.source_url = data.get("source_url", "")
        self.wiki_url = data.get("wiki_url", "")
        self.discord_url = data.get("discord_url", "")
        self.donation_urls = data["donation_urls"]
        self.gallery = data["gallery"]

    @classmethod
    @cache(ttl=timedelta(hours=1), key="modrinth_project:{project}", condition=NOT_NONE)
    async def from_id(cls, project: str):
        url = f"{API_BASE_URL}/project/{project}"
        try:
            async with httpx.AsyncClient(http2=True) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.RequestError as exc:
            msg = f"An error occurred while requesting {exc.request.url!r}."
            raise RuntimeError(msg) from exc
        except httpx.HTTPStatusError as exc:
            msg = (
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )
            raise RuntimeError(msg) from exc

        try:
            data = response.json()
        except ValueError as exc:
            msg = f"Failed to parse JSON response from {url}."
            raise RuntimeError(msg) from exc

        return cls(project, data)

    @property
    def is_server_side(self) -> bool:
        return self.server_side in {"optional", "required"}

    @property
    def is_client_side(self) -> bool:
        return self.client_side in {"optional", "required"}

    async def get_latest_version(self) -> "ModrinthVersion":
        return await ModrinthVersion.from_id(self, self.versions[-1])


class ModrinthSearch:
    def __init__(
        self,
        query: str,
        categories: list | None = None,
        versions: list | None = None,
        project_types: list[ProjectType] | None = None,
        licenses: list | None = None,
        index: str = "relevance",
        offset: int = 0,
        limit: int = 10,
        filters: str = "",
    ) -> None:
        self.query = query
        self.categories = categories or []
        self.versions = versions or []
        self.project_types = project_types or []
        self.licenses = licenses or []
        self.index = index
        self.offset = offset
        self.limit = limit
        self.filters = filters

    @cache(ttl=timedelta(hours=1), condition=NOT_NONE)
    async def fetch(self) -> None:
        facets = self._build_facets()
        url = (
            f"{API_BASE_URL}/search?query={self.query}&index={self.index}"
            f"&offset={self.offset}&limit={self.limit}&filters={self.filters}{facets}"
        )

        try:
            async with httpx.AsyncClient(http2=True) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.RequestError as exc:
            msg = f"An error occurred while requesting {exc.request.url!r}."
            raise RuntimeError(msg) from exc
        except httpx.HTTPStatusError as exc:
            msg = (
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )
            raise RuntimeError(msg) from exc

        try:
            data = response.json()
        except ValueError as exc:
            msg = f"Failed to parse JSON response from {url}."
            raise RuntimeError(msg) from exc

        self.hits = [await ModrinthProject.from_id(hit["project_id"]) for hit in data["hits"]]
        self.offset = data["offset"]
        self.limit = data["limit"]
        self.total = data["total_hits"]

    def _build_facets(self) -> str:
        facets = []
        if self.categories:
            facets.append(f'["categories:{",".join(self.categories)}"]')
        if self.versions:
            facets.append(f'["versions:{",".join(self.versions)}"]')
        if self.project_types:
            facets.append(f'["project_type:{",".join(pt.value for pt in self.project_types)}"]')
        if self.licenses:
            facets.append(f'["license:{",".join(self.licenses)}"]')

        return f"&facets=[{",".join(facets)}]" if facets else ""


class ModrinthVersion:
    def __init__(self, project: ModrinthProject, version: str, data: dict):
        if not isinstance(project, ModrinthProject):
            msg = "project must be a ModrinthProject instance"
            raise TypeError(msg)
        if version not in project.versions:
            msg = "version must be a valid version of the project"
            raise ValueError(msg)

        self.project = project
        self.version = version
        self.project_id = data["project_id"]
        self.author_id = data["author_id"]
        self.date_published = data["date_published"]
        self.downloads = data["downloads"]
        self.files = data["files"]
        self.name = data["name"]
        self.version_number = data["version_number"]
        self.game_versions = data["game_versions"]
        self.version_type = data["version_type"]
        self.loaders = data["loaders"]
        self.featured = data["featured"]
        self.changelog = data["changelog"]
        self.dependencies = data["dependencies"]
        self.changelog_url = data["changelog_url"]

    @classmethod
    @cache(ttl=timedelta(hours=1), key="modrinth_version:{project}:{version}", condition=NOT_NONE)
    async def from_id(cls, project: ModrinthProject, version: str):
        url = f"{API_BASE_URL}/version/{version}"
        try:
            async with httpx.AsyncClient(http2=True) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.RequestError as exc:
            msg = f"An error occurred while requesting {exc.request.url!r}."
            raise RuntimeError(msg) from exc
        except httpx.HTTPStatusError as exc:
            msg = (
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )
            raise RuntimeError(msg) from exc

        try:
            data = response.json()
        except ValueError as exc:
            msg = f"Failed to parse JSON response from {url}."
            raise RuntimeError(msg) from exc

        return cls(project, version, data)
