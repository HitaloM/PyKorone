# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import CallbackQuery, Message

from korone.decorators import router
from korone.filters.command import Command, CommandObject
from korone.modules.weather.callback_data import WeatherCallbackData
from korone.modules.weather.utils.api import get_weather_observations, search_location
from korone.modules.weather.utils.types import WeatherResult, WeatherSearch
from korone.modules.weather.utils.weather_icons import get_status_emoji
from korone.utils.caching import cache
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _
from korone.utils.pagination import Pagination


async def fetch_location_data(command_args: str, language: str) -> dict:
    cache_key = f"weather_location_{command_args}"
    data = await cache.get(cache_key) or await search_location(command_args, language)
    if data:
        await cache.set(cache_key, data, expire=3600)
    return data


def format_weather_text(weather_result: WeatherResult) -> str:
    return (
        f"<b>{weather_result.city}, {weather_result.admin_district}, "
        f"{weather_result.country}</b>:\n\n"
        f"🌡️ <b>{_('Temperature:')}</b> {weather_result.temperature}°C\n"
        f"🌡️ <b>{_('Temperature feels like:')}</b> {weather_result.temperature_feels_like}°C\n"
        f"💧 <b>{_('Air humidity:')}</b> {weather_result.relative_humidity}%\n"
        f"💨 <b>{_('Wind Speed:')}</b> {weather_result.wind_speed} km/h\n\n"
        f"- {get_status_emoji(weather_result.icon_code)} <i>{weather_result.wx_phrase_long}</i>"
    )


@router.message(Command(commands=["weather", "clima"]))
async def get_weather(client: Client, message: Message) -> None:
    command = CommandObject(message).parse()

    if not command.args or len(command.args) <= 1:
        await message.reply_text(
            _(
                "No location provided. You should provide a location. "
                "Example: <code>/weather Rio de Janeiro</code>"
            )
        )
        return

    current_locale = get_i18n().current_locale_babel
    language = (
        f"{current_locale.language}-{current_locale.territory}"
        if current_locale.language and current_locale.territory
        else "en-US"
    )

    data = await fetch_location_data(command.args, language)
    if not data:
        await message.reply_text(_("Failed to fetch weather data."))
        return

    weather_search = WeatherSearch.model_validate(data.get("location", {}))
    locations = list(
        zip(
            weather_search.address, weather_search.latitude, weather_search.longitude, strict=False
        )
    )

    if not locations:
        await message.reply_text(_("No locations found for the provided query."))
        return

    pagination = Pagination(
        objects=locations,
        page_data=lambda page: WeatherCallbackData(page=page).pack(),
        item_data=lambda item, _: WeatherCallbackData(latitude=item[1], longitude=item[2]).pack(),
        item_title=lambda item, _: item[0],
    )

    keyboard_markup = pagination.create(page=1)
    await cache.set(f"weather_locations_{message.chat.id}", locations, expire=300)

    await message.reply(_("Please select a location:"), reply_markup=keyboard_markup)


@router.callback_query(WeatherCallbackData.filter())
async def callback_weather(client: Client, callback_query: CallbackQuery) -> None:
    if not callback_query.data:
        return

    data = WeatherCallbackData.unpack(callback_query.data)
    chat_id = callback_query.message.chat.id

    if data.page:
        locations = await cache.get(f"weather_locations_{chat_id}")
        if not locations:
            await callback_query.answer(_("Session expired. Please try again."), show_alert=True)
            return

        pagination = Pagination(
            objects=locations,
            page_data=lambda page: WeatherCallbackData(page=page).pack(),
            item_data=lambda item, _: WeatherCallbackData(
                latitude=item[1], longitude=item[2]
            ).pack(),
            item_title=lambda item, _: item[0],
        )
        keyboard_markup = pagination.create(page=data.page)

        await callback_query.edit_message_reply_markup(reply_markup=keyboard_markup)
        return

    current_locale = get_i18n().current_locale_babel
    language = (
        f"{current_locale.language}-{current_locale.territory}"
        if current_locale.language and current_locale.territory
        else "en-US"
    )

    if data.latitude and data.longitude:
        weather_data = await get_weather_observations(data.latitude, data.longitude, language)
        if not weather_data:
            await callback_query.answer(_("Failed to fetch weather data."), show_alert=True)
            return

        location_data = weather_data.get("v3-location-point", {}).get("location", {})
        weather_observation = weather_data.get("v3-wx-observations-current", {})

        if not location_data or not weather_observation:
            await callback_query.answer(_("Incomplete weather data received."), show_alert=True)
            return

        weather_result = WeatherResult.model_validate({
            **weather_observation,
            "id": location_data.get("locId"),
            "city": location_data.get("city"),
            "adminDistrict": location_data.get("adminDistrict"),
            "country": location_data.get("country"),
        })

        text = format_weather_text(weather_result)
        await callback_query.edit_message_text(text=text)
