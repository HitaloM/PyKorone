from __future__ import annotations

from dataclasses import dataclass
from subprocess import PIPE
from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from anyio import Lock, Path, run_process
from stfu_tg import Code, Doc, Section, Template, VList

from korone.config import CONFIG
from korone.constants import TELEGRAM_MESSAGE_LENGTH_LIMIT
from korone.filters.cmd import CMDFilter
from korone.filters.user_status import IsOP
from korone.logger import get_logger
from korone.modules.op.callbacks import OpUpdateCallback
from korone.modules.op.utils import find_repo_root, restart_bot, save_restart_marker
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from collections.abc import Iterable

    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import Message
    from stfu_tg.doc import Element

logger = get_logger(__name__)
UPDATE_LOCK = Lock()


@dataclass(slots=True)
class CommitInfo:
    short_hash: str
    author: str
    date: str
    summary: str


class GitCommandError(RuntimeError):
    def __init__(self, command: list[str], stdout: str, stderr: str) -> None:
        msg = f"Git command failed: {' '.join(command)}"
        super().__init__(msg)
        self.command = command
        self.stdout = stdout
        self.stderr = stderr


async def run_git(command: list[str], *, cwd: Path) -> tuple[int, str, str]:
    result = await run_process(command, stdout=PIPE, stderr=PIPE, cwd=cwd)
    stdout = (result.stdout or b"").decode().strip()
    stderr = (result.stderr or b"").decode().strip()
    return result.returncode, stdout, stderr


async def get_upstream(cwd: Path) -> str:
    code, stdout, _stderr = await run_git(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=cwd)
    if code != 0 or not stdout:
        return "origin/main"
    return stdout


async def fetch_new_commits(cwd: Path) -> tuple[list[CommitInfo], str]:
    code, stdout, stderr = await run_git(["git", "fetch", "--prune", "origin"], cwd=cwd)
    if code != 0:
        raise GitCommandError(["git", "fetch", "--prune", "origin"], stdout, stderr)

    upstream = await get_upstream(cwd)
    log_format = "%h\t%an\t%ad\t%s"
    code, stdout, stderr = await run_git(
        ["git", "log", "--pretty=format:" + log_format, "--date=short", f"HEAD..{upstream}"], cwd=cwd
    )
    if code != 0:
        raise GitCommandError(["git", "log", f"HEAD..{upstream}"], stdout, stderr)

    commits: list[CommitInfo] = []
    if stdout:
        for line in stdout.splitlines():
            parts = line.split("\t", maxsplit=3)
            if len(parts) != 4:
                continue
            short_hash, author, date, summary = parts
            commits.append(CommitInfo(short_hash=short_hash, author=author, date=date, summary=summary))

    return commits, upstream


def build_commit_items(commits: Iterable[CommitInfo]) -> list[Element]:
    items: list[Element] = [
        Template(
            _("{hash} {summary} - {author}, {date}"),
            hash=Code(commit.short_hash),
            summary=commit.summary,
            author=commit.author,
            date=commit.date,
        )
        for commit in commits
    ]
    return items


def chunk_commit_docs(commits: list[CommitInfo], upstream: str) -> list[str]:
    header = Section(
        Template(_("Upstream: {upstream}"), upstream=Code(upstream)),
        Template(_("New commits: {count}"), count=Code(len(commits))),
        title=_("Update status"),
    )

    if not commits:
        return [str(Doc(header, Section(_("No updates available."), title=_("Commits"))))]

    items = build_commit_items(commits)
    docs: list[str] = []
    current: list[Element] = []

    limit = TELEGRAM_MESSAGE_LENGTH_LIMIT - 32

    for item in items:
        candidate = [*current, item]
        candidate_doc = Doc(header, Section(VList(*candidate), title=_("Commits")))
        if len(str(candidate_doc)) > limit and current:
            docs.append(str(Doc(header, Section(VList(*current), title=_("Commits")))))
            current = [item]
            continue
        if len(str(candidate_doc)) > limit:
            docs.append(str(candidate_doc))
            current = []
            continue
        current = candidate

    if current:
        docs.append(str(Doc(header, Section(VList(*current), title=_("Commits")))))

    return docs


@flags.help(description=l_("Fetch updates from git and restart the bot."))
class OpUpdateHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(("update", "upgrade")), IsOP(is_op=True))

    async def handle(self) -> None:
        repo_root = await find_repo_root(await Path(__file__).resolve())

        try:
            commits, upstream = await fetch_new_commits(repo_root)
        except GitCommandError as exc:
            error_text = exc.stderr or exc.stdout or _("Unknown git error")
            await self.event.reply(str(Doc(Section(Template(_("Update failed: {error}"), error=Code(error_text))))))
            return

        docs = chunk_commit_docs(commits, upstream)
        reply_markup = None
        if commits and self.event.from_user:
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(
                    text=_("Update and restart"),
                    callback_data=OpUpdateCallback(initiator_id=self.event.from_user.id).pack(),
                )
            )
            reply_markup = builder.as_markup()

        for index, text in enumerate(docs):
            if index == 0:
                await self.event.reply(text, reply_markup=reply_markup)
            else:
                await self.event.reply(text)


@flags.help(exclude=True)
class OpUpdateCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (OpUpdateCallback.filter(),)

    async def handle(self) -> None:
        if not self.event.from_user:
            return

        if self.event.from_user.id not in CONFIG.operators:
            await self.event.answer(_("Not allowed."), show_alert=True)
            return

        callback_data = cast("OpUpdateCallback", self.callback_data)
        if callback_data.initiator_id != self.event.from_user.id:
            await self.event.answer(_("Only the requester can confirm this update."), show_alert=True)
            return

        await self.event.answer(_("Updating..."))

        async with UPDATE_LOCK:
            await self.check_for_message()
            await self.edit_text(_("Applying updates and restarting..."))

            await logger.ainfo("op_update: starting git pull", user_id=self.event.from_user.id)

            repo_root = await find_repo_root(await Path(__file__).resolve())
            code, stdout, stderr = await run_git(["git", "pull"], cwd=repo_root)
            if code != 0:
                error_text = stderr or stdout or _("Unknown git error")
                await self.edit_text(str(Doc(Section(Template(_("Update failed: {error}"), error=Code(error_text))))))
                await logger.awarning("op_update: git pull failed", error=error_text)
                return

            await logger.ainfo("op_update: git pull complete", output=stdout)
            await self.edit_text(_("Update complete. Restarting now..."))
            message = cast("Message", self.event.message)
            await save_restart_marker(chat_id=message.chat.id, message_id=message.message_id, action="update")
            await restart_bot()
