# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress
from datetime import datetime

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.minecraft.callback_data import (
    GetModrinthProjectCallback,
    ModrinthDetailsCallback,
    ModrinthPageCallback,
)
from korone.modules.minecraft.utils.modrinth import ModrinthProject, ModrinthSearch, ProjectType
from korone.utils.i18n import gettext as _
from korone.utils.pagination import Pagination


@router.message(Command("modrinth"))
async def handle_modrinth_command(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()

    if not command.args:
        await message.reply(
            _("You need to provide a search query. Example: <code>/modrinth sodium</code>.")
        )
        return

    projects = await fetch_modrinth_projects(command.args)
    if not projects:
        await message.reply(_("No projects found."))
        return

    if len(projects) == 1:
        await send_project_details(message, projects[0])
        return

    keyboard = create_pagination_keyboard(projects, command.args, 1)
    await message.reply(
        _("Search results for: <b>{query}</b>").format(query=command.args),
        reply_markup=keyboard,
    )


@router.callback_query(GetModrinthProjectCallback.filter())
async def handle_get_modrinth_project_callback(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        return

    callback_data = GetModrinthProjectCallback.unpack(callback.data)
    project = await ModrinthProject.from_id(callback_data.project_id)
    await send_project_details(callback.message, project)


@router.callback_query(ModrinthPageCallback.filter())
async def handle_modrinth_pagination_callback(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        return

    callback_data = ModrinthPageCallback.unpack(callback.data)
    projects = await fetch_modrinth_projects(callback_data.query)
    keyboard = create_pagination_keyboard(projects, callback_data.query, callback_data.page)

    with suppress(MessageNotModified):
        await callback.edit_message_reply_markup(reply_markup=keyboard)


@router.callback_query(ModrinthDetailsCallback.filter())
async def handle_modrinth_details_callback(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        return

    callback_data = ModrinthDetailsCallback.unpack(callback.data)
    project = await ModrinthProject.from_id(callback_data.project_id)

    details_text = build_project_details_text(project)
    await callback.answer(details_text, show_alert=True, cache_time=60)


async def fetch_modrinth_projects(query: str) -> list[ModrinthProject]:
    search = ModrinthSearch(query=query, limit=40)
    await search.fetch()
    return search.hits


async def send_project_details(message: Message, project: ModrinthProject) -> None:
    modrinth_url = f"https://modrinth.com/{project.project_type.value}/{project.id}"
    keyboard = create_project_keyboard(project, modrinth_url)
    text = await build_project_text(project)

    if message.chat.type == ChatType.PRIVATE:
        await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)
        return

    with suppress(MessageNotModified):
        await message.edit(text, reply_markup=keyboard, disable_web_page_preview=True)


def create_project_keyboard(project: ModrinthProject, url: str) -> InlineKeyboardMarkup:
    keyboard = (
        InlineKeyboardBuilder()
        .button(text=_("Open in Modrinth"), url=url)
        .button(text=_("Details"), callback_data=ModrinthDetailsCallback(project_id=project.id))
    )
    return keyboard.as_markup()


def build_project_details_text(project: ModrinthProject) -> str:
    download_count = format_number(project.downloads)
    followers_count = format_number(project.followers)
    published_date = format_date(project.published)
    updated_date = format_date(project.updated)
    categories = ", ".join(project.categories)

    return (
        _("Downloads: {downloads}\n").format(downloads=download_count)
        + _("Followers: {followers}\n").format(followers=followers_count)
        + _("Published: {published}\n").format(published=published_date)
        + _("Updated: {updated}\n").format(updated=updated_date)
        + _("Categories: {categories}\n").format(categories=categories)
    )


async def build_project_text(project: ModrinthProject) -> str:
    text = f"<b>{project.name}</b>"
    if project.project_type:
        text += f" [{format_project_type(project.project_type)}]"

    text += f"\n<i>{project.description}</i>\n\n"

    if project.project_type in {ProjectType.MOD, ProjectType.MODPACK} and project.loaders:
        mod_loaders = format_mod_loaders(project.loaders)
        environments = ", ".join(get_supported_environments(project))

        text += _("<b>Platforms</b>: {platforms}\n").format(platforms=mod_loaders)
        text += _("<b>Supported environments</b>: {environments}\n").format(
            environments=environments
        )

    latest_version = await project.get_latest_version()
    text += _("<b>Latest version</b>: {version}").format(version=latest_version.version_number)

    return text


def format_number(number: int) -> str:
    return f"{number:,}".replace(",", ".")


def format_date(date_str: str) -> str:
    date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    return date.strftime("%d/%m/%Y")


def format_project_type(project_type: ProjectType) -> str | None:
    return {
        ProjectType.MOD: _("Mod"),
        ProjectType.MODPACK: _("Modpack"),
        ProjectType.RESOURCEPACK: _("Resource pack"),
        ProjectType.SHADER: _("Shader pack"),
    }.get(project_type)


def format_mod_loaders(loaders: list[str]) -> str:
    return (
        ", ".join(loaders)
        .replace("fabric", "Fabric")
        .replace("neoforge", "NeoForge")
        .replace("forge", "Forge")
        .replace("quilt", "Quilt")
        .replace("datapack", "Data Pack")
    )


def get_supported_environments(project: ModrinthProject) -> list[str]:
    environments = []
    if project.is_client_side:
        environments.append("Client-side")
    if project.is_server_side:
        environments.append("Server-side")
    return environments


def create_pagination_keyboard(
    projects: list[ModrinthProject], query: str, page: int
) -> InlineKeyboardMarkup:
    pagination = Pagination(
        projects,
        item_data=lambda p, _: GetModrinthProjectCallback(project_id=p.id).pack(),
        item_title=lambda p, _: p.name,
        page_data=lambda pg: ModrinthPageCallback(query=query, page=pg).pack(),
    )
    return pagination.create(page, lines=8)
