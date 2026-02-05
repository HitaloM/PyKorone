from __future__ import annotations

import json
import os
import sys
import time

from anyio import Path, sleep
from stfu_tg import Code, Doc, Template

from korone import aredis, bot
from korone.logger import get_logger
from korone.utils.i18n import gettext as _

logger = get_logger(__name__)
RESTART_MARKER_KEY = "op:restart_marker"


async def find_repo_root(start: Path) -> Path:
    for parent in (start, *start.parents):
        if await (parent / ".git").exists() or await (parent / "pyproject.toml").exists():
            return parent
    return start


async def restart_bot() -> None:
    repo_root = await find_repo_root(await Path(__file__).resolve())
    await logger.ainfo("op_restart: restarting bot process")
    await sleep(0.3)
    os.chdir(repo_root)
    os.execv(sys.executable, [sys.executable, "-m", "korone", *sys.argv[1:]])


async def save_restart_marker(*, chat_id: int, message_id: int | None, action: str) -> None:
    payload = {"chat_id": chat_id, "message_id": message_id, "action": action, "started_at": time.time()}
    await aredis.set(RESTART_MARKER_KEY, json.dumps(payload))


async def _pop_restart_marker() -> dict[str, object] | None:
    raw = await aredis.get(RESTART_MARKER_KEY)
    if not raw:
        return None

    await aredis.delete(RESTART_MARKER_KEY)

    try:
        text = raw.decode() if isinstance(raw, (bytes, bytearray)) else str(raw)
        payload = json.loads(text)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        await logger.awarning("op_restart: failed to decode restart marker", error=str(exc))
        return None

    if isinstance(payload, dict):
        return payload
    return None


async def notify_restart_complete() -> None:
    payload = await _pop_restart_marker()
    if not payload:
        return

    chat_id = payload.get("chat_id")
    started_at = payload.get("started_at")
    message_id = payload.get("message_id")

    if not isinstance(chat_id, int) or not isinstance(started_at, (int, float)):
        await logger.awarning("op_restart: restart marker missing required fields")
        return

    elapsed = max(0.0, time.time() - float(started_at))
    seconds_text = f"{elapsed:.1f}"
    text = str(Doc(Template(_("Restart complete in {seconds}s."), seconds=Code(seconds_text))))

    if isinstance(message_id, int):
        try:
            await bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id)
        except Exception as exc:  # noqa: BLE001
            await logger.awarning("op_restart: edit restart message failed", error=str(exc))
        else:
            return

    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as exc:  # noqa: BLE001
        await logger.awarning("op_restart: restart completion notify failed", error=str(exc))
