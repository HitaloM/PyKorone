from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, cast

from aiogram import flags
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import User
from ass_tg.types import OptionalArg
from stfu_tg import Code, Doc, Template, Title, UserLink

from korone.args.users import KoroneUserArg
from korone.db.models.chat import ChatModel
from korone.db.repositories.chat import ChatRepository
from korone.filters.cmd import CMDFilter
from korone.modules.users.callbacks import ProfileAudioSendCallback, ProfileAudiosPageCallback
from korone.modules.utils_.message import is_real_reply
from korone.modules.utils_.pagination import Pagination
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.client.bot import Bot
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Audio, InlineKeyboardMarkup, Message
    from aiogram.types.user_profile_audios import UserProfileAudios
    from ass_tg.types.base_abc import ArgFabric

PROFILE_AUDIOS_PER_PAGE = 8
MAX_AUDIO_BUTTON_TEXT_LENGTH = 56


def _display_name(user: ChatModel) -> str:
    return user.first_name_or_title or _("User")


def _audio_title(audio: Audio, fallback_index: int | None = None) -> str:
    if audio.performer and audio.title:
        return f"{audio.performer} - {audio.title}"

    if audio.title:
        return audio.title

    if audio.file_name:
        return audio.file_name

    if fallback_index is not None:
        return _("Audio #{index}").format(index=fallback_index)

    return _("Unknown audio")


def _format_duration(seconds: int) -> str:
    minutes, sec = divmod(max(0, seconds), 60)
    hours, min_ = divmod(minutes, 60)

    if hours:
        return f"{hours}:{min_:02}:{sec:02}"

    return f"{min_}:{sec:02}"


def _truncate_text(text: str, max_length: int = MAX_AUDIO_BUTTON_TEXT_LENGTH) -> str:
    if len(text) <= max_length:
        return text

    return f"{text[: max_length - 1]}…"


def _build_featured_audio_label(featured_audio: Audio | None) -> str:
    if not featured_audio:
        return _("No featured audio")

    return _("{title} ({duration})").format(
        title=_audio_title(featured_audio), duration=_format_duration(featured_audio.duration)
    )


def _chat_model_to_user(chat_model: ChatModel, bot: Bot) -> User:
    return User(
        id=chat_model.chat_id,
        is_bot=chat_model.is_bot,
        first_name=_display_name(chat_model),
        last_name=chat_model.last_name,
        username=chat_model.username,
    ).as_(bot)


def _build_profile_audios_text(
    target_user: ChatModel, total_count: int, featured_audio: Audio | None, page: int
) -> str:
    last_page = max(1, math.ceil(total_count / PROFILE_AUDIOS_PER_PAGE))

    doc = Doc(Title(_("Profile audios")))
    doc += Template(_("User: {user}"), user=UserLink(user_id=target_user.chat_id, name=_display_name(target_user)))
    doc += Template(_("Total audios: {count}"), count=Code(str(total_count)))
    doc += Template(_("Featured: {featured}"), featured=_build_featured_audio_label(featured_audio))

    if total_count > 0:
        doc += Template(_("Page: {current}/{last}"), current=Code(str(page)), last=Code(str(last_page)))
        doc += _("Select an audio below to send it.")

    return str(doc)


def _build_audio_button_title(index: int, audios_map: dict[int, Audio]) -> str:
    audio = audios_map.get(index)
    if audio is None:
        return _("Audio #{index}").format(index=index + 1)

    title = _audio_title(audio, fallback_index=index + 1)
    return _truncate_text(f"{index + 1}. {title}")


def _build_profile_audios_keyboard(
    page_audios: list[Audio], total_count: int, page: int, target_user_id: int, requester_user_id: int
) -> InlineKeyboardMarkup:
    page_offset = (page - 1) * PROFILE_AUDIOS_PER_PAGE
    audios_map = dict(enumerate(page_audios, start=page_offset))

    pagination = Pagination(
        objects=list(range(total_count)),
        page_data=lambda page_number: ProfileAudiosPageCallback(
            target_user_id=target_user_id, requester_user_id=requester_user_id, page=page_number
        ).pack(),
        item_data=lambda item, _: ProfileAudioSendCallback(
            target_user_id=target_user_id, requester_user_id=requester_user_id, offset=item
        ).pack(),
        item_title=lambda item, _: _build_audio_button_title(item, audios_map),
    )

    return pagination.create(page=page, lines=PROFILE_AUDIOS_PER_PAGE, columns=1)


async def _resolve_target_user(message: Message, parsed_target: ChatModel | None) -> ChatModel | None:
    if parsed_target:
        return parsed_target

    if message.reply_to_message and is_real_reply(message) and message.reply_to_message.from_user:
        return await ChatRepository.upsert_user(message.reply_to_message.from_user)

    if message.from_user:
        user_model = await ChatRepository.get_by_chat_id(message.from_user.id)
        if user_model:
            return user_model

        return await ChatRepository.upsert_user(message.from_user)

    return None


async def _fetch_profile_audio_page(tg_user: User, requested_page: int) -> tuple[int, int, list[Audio], Audio | None]:
    page = max(1, requested_page)
    offset = (page - 1) * PROFILE_AUDIOS_PER_PAGE

    page_result: UserProfileAudios = await tg_user.get_profile_audios(offset=offset, limit=PROFILE_AUDIOS_PER_PAGE)
    total_count = page_result.total_count

    if total_count <= 0:
        return 1, 0, [], None

    last_page = max(1, math.ceil(total_count / PROFILE_AUDIOS_PER_PAGE))
    if page > last_page:
        page = last_page
        offset = (page - 1) * PROFILE_AUDIOS_PER_PAGE
        page_result = await tg_user.get_profile_audios(offset=offset, limit=PROFILE_AUDIOS_PER_PAGE)

    featured_audio: Audio | None = page_result.audios[0] if page == 1 and page_result.audios else None

    if featured_audio is None:
        featured_result = await tg_user.get_profile_audios(offset=0, limit=1)
        featured_audio = featured_result.audios[0] if featured_result.audios else None

    return page, total_count, page_result.audios, featured_audio


@flags.help(description=l_("Shows a user's profile audios."))
@flags.disableable(name="profileaudios")
class UserProfileAudiosHandler(KoroneMessageHandler):
    @classmethod
    async def handler_args(cls, message: Message | None, data: dict[str, Any]) -> dict[str, ArgFabric]:
        return {"user": OptionalArg(KoroneUserArg(l_("User")))}

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("profileaudios", "profileaudio", "paudios")),)

    async def handle(self) -> None:
        target_user = await _resolve_target_user(self.event, self.data.get("user"))
        if not target_user:
            await self.event.reply(_("Could not identify user."))
            return

        if target_user.type != ChatType.PRIVATE:
            await self.event.reply(_("The selected target is not a user."))
            return

        if target_user.is_bot:
            await self.event.reply(_("Bots do not have profile audios."))
            return

        if not self.event.from_user:
            msg = "User information is not available in the handler context."
            raise RuntimeError(msg)

        tg_user = _chat_model_to_user(target_user, self.bot)

        try:
            page, total_count, page_audios, featured_audio = await _fetch_profile_audio_page(tg_user, requested_page=1)
        except TelegramBadRequest:
            await self.event.reply(_("Could not fetch profile audios for this user."))
            return

        text = _build_profile_audios_text(target_user, total_count, featured_audio, page)

        if total_count <= 0:
            await self.event.reply(_("This user has no profile audios."))
            return

        keyboard = _build_profile_audios_keyboard(
            page_audios=page_audios,
            total_count=total_count,
            page=page,
            target_user_id=target_user.chat_id,
            requester_user_id=self.event.from_user.id,
        )

        await self.event.reply(text, reply_markup=keyboard)


@flags.help(exclude=True)
class UserProfileAudiosPageHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (ProfileAudiosPageCallback.filter(),)

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = cast("ProfileAudiosPageCallback", self.callback_data)

        if self.event.from_user.id != callback_data.requester_user_id:
            await self.event.answer(_("You are not allowed to use this button."), show_alert=True)
            return

        target_user = await ChatRepository.get_by_chat_id(callback_data.target_user_id)
        if not target_user:
            target_user = ChatModel.user_from_id(callback_data.target_user_id)

        tg_user = _chat_model_to_user(target_user, self.bot)

        try:
            page, total_count, page_audios, featured_audio = await _fetch_profile_audio_page(
                tg_user, requested_page=callback_data.page
            )
        except TelegramBadRequest:
            await self.event.answer(_("Could not fetch profile audios for this user."), show_alert=True)
            return

        message = cast("Message", self.event.message)
        text = _build_profile_audios_text(target_user, total_count, featured_audio, page)

        if total_count <= 0:
            await message.edit_text(_("This user has no profile audios."), reply_markup=None)
            await self.event.answer()
            return

        keyboard = _build_profile_audios_keyboard(
            page_audios=page_audios,
            total_count=total_count,
            page=page,
            target_user_id=callback_data.target_user_id,
            requester_user_id=callback_data.requester_user_id,
        )

        try:
            await message.edit_text(text, reply_markup=keyboard)
        except TelegramBadRequest as err:
            if "message is not modified" not in err.message:
                raise

        await self.event.answer()


@flags.help(exclude=True)
class UserProfileAudioSendHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (ProfileAudioSendCallback.filter(),)

    async def handle(self) -> None:
        await self.check_for_message()

        callback_data = cast("ProfileAudioSendCallback", self.callback_data)

        if self.event.from_user.id != callback_data.requester_user_id:
            await self.event.answer(_("You are not allowed to use this button."), show_alert=True)
            return

        target_user = await ChatRepository.get_by_chat_id(callback_data.target_user_id)
        if not target_user:
            target_user = ChatModel.user_from_id(callback_data.target_user_id)

        tg_user = _chat_model_to_user(target_user, self.bot)

        try:
            result = await tg_user.get_profile_audios(offset=callback_data.offset, limit=1)
        except TelegramBadRequest:
            await self.event.answer(_("Could not fetch profile audios for this user."), show_alert=True)
            return

        if not result.audios:
            await self.event.answer(_("This audio is no longer available."), show_alert=True)
            return

        audio = result.audios[0]
        caption = Template(
            _("From {user}'s profile: {audio}"),
            user=UserLink(user_id=target_user.chat_id, name=_display_name(target_user)),
            audio=_audio_title(audio, fallback_index=callback_data.offset + 1),
        ).to_html()

        message = cast("Message", self.event.message)

        try:
            await message.reply_audio(audio=audio.file_id, caption=caption)
        except TelegramBadRequest:
            await self.event.answer(_("Could not send this audio right now."), show_alert=True)
            return

        await self.event.answer(_("Audio sent."))
