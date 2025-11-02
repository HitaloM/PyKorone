from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Tuple

from aiogram.types import Message
from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import In
from stfu_tg import Bold, Code, Doc, KeyValue, Section, Template, UserLink
from stfu_tg.doc import Element

from sophie_bot.db.models import AIUsageModel
from sophie_bot.db.models.chat import ChatModel, ChatType
from sophie_bot.utils.i18n import gettext as _

# Types
TopMap = MutableMapping[str, int]


def _normalize_days(days: Mapping[Any, int]) -> Dict[date, int]:
    """Normalize keys of days mapping to `date`.

    Beanie might deserialize map keys as strings; ensure we compare date objects.
    """
    normalized: Dict[date, int] = {}
    for k, v in days.items():
        if isinstance(k, date):
            normalized[k] = int(v)
        elif isinstance(k, str):
            # Expecting ISO format (YYYY-MM-DD)
            try:
                normalized[date.fromisoformat(k)] = int(v)
            except ValueError:
                # Skip unparseable keys
                continue
    return normalized


def _sum_in_range(days: Mapping[date, int], start: date, end: date) -> int:
    return sum(v for d, v in days.items() if start <= d <= end)


def _add_count(m: TopMap, key: str, value: int) -> None:
    if value <= 0:
        return
    m[key] = m.get(key, 0) + value


def _top_n(items: Mapping[str, int], n: int) -> List[Tuple[str, int]]:
    return sorted(items.items(), key=lambda x: x[1], reverse=True)[:n]


def _display_name(chat: ChatModel) -> str | Element:
    if chat.type == ChatType.private:
        return UserLink(chat.chat_id, chat.first_name_or_title)
    # groups/supergroups/channels
    return chat.first_name_or_title


def _format_top(
    ranking: Iterable[Tuple[str, int]],
    chat_by_id: Mapping[str, ChatModel],
) -> List[Template]:
    lines: List[Template] = []
    for idx, (iid, count) in enumerate(ranking, start=1):
        chat = chat_by_id.get(iid)
        if not chat:
            # Skip if chat not found (rare)
            continue
        lines.append(
            Template(
                "{idx}. {name} — {count}",
                idx=Code(idx),
                name=_display_name(chat),
                count=Code(count),
            )
        )
    if not lines:
        lines.append(Template("{msg}", msg=Code(_("No data"))))
    return lines


async def op_ai_stats_handler(message: Message) -> None:
    today = date.today()
    start_week = today - timedelta(days=today.weekday())  # Monday as start of the week
    start_month = today.replace(day=1)

    # Fetch all AI usage documents
    usages = await AIUsageModel.find_all().to_list()  # type: ignore[attr-defined]

    # Totals
    total_today = 0
    total_week = 0
    total_month = 0

    # Per-period counters per chat (by chat_iid str)
    chats_today: TopMap = {}
    chats_week: TopMap = {}
    chats_month: TopMap = {}

    # Collect chat IIDs we'll need to render names
    iids_needed: set[str] = set()

    for u in usages:
        days = _normalize_days(u.days)
        t = _sum_in_range(days, today, today)
        w = _sum_in_range(days, start_week, today)
        m = _sum_in_range(days, start_month, today)

        # u.chat.id is PydanticObjectId, convert to str for dict keys
        iid_str = str(u.chat.ref.id)

        if t > 0:
            total_today += t
            _add_count(chats_today, iid_str, t)
            iids_needed.add(iid_str)
        if w > 0:
            total_week += w
            _add_count(chats_week, iid_str, w)
            iids_needed.add(iid_str)
        if m > 0:
            total_month += m
            _add_count(chats_month, iid_str, m)
            iids_needed.add(iid_str)

    # Load chat models for all iids that had usage
    chat_models: list[ChatModel] = []
    chat_by_id: dict[str, ChatModel] = {}
    if iids_needed:
        # Convert back to ObjectIds via ChatModel.find(In(ChatModel.id, ...))
        ids = [PydanticObjectId(i) for i in iids_needed]
        chat_models = await ChatModel.find(In(ChatModel.id, ids)).to_list()
        chat_by_id = {str(c.id): c for c in chat_models}

    # Split into groups vs users
    def filter_type(data: Mapping[str, int], type_: ChatType) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for iid, count in data.items():
            chat = chat_by_id.get(iid)
            if not chat:
                continue
            if chat.type == type_:
                out[iid] = count
        return out

    top_chats_today = _top_n({k: v for k, v in filter_type(chats_today, ChatType.group).items()}, 5)
    # Include supergroups and channels as chats as well
    extra_chats_today = _top_n(
        {
            k: v
            for k, v in chats_today.items()
            if chat_by_id.get(k) and chat_by_id[k].type in {ChatType.supergroup, ChatType.channel}
        },
        5,
    )
    # Merge and re-sort, keeping up to 5 unique
    merged_today: Dict[str, int] = {}
    for k, v in [*top_chats_today, *extra_chats_today]:
        if k not in merged_today:
            merged_today[k] = v
        if len(merged_today) >= 5:
            break
    top_chats_today_list = _top_n(merged_today, 5)

    def top_chats_period(data: Mapping[str, int]) -> List[Tuple[str, int]]:
        # Combine group/supergroup/channel
        combined: Dict[str, int] = {}
        for iid, count in data.items():
            chat = chat_by_id.get(iid)
            if not chat:
                continue
            if chat.type in {ChatType.group, ChatType.supergroup, ChatType.channel}:
                combined[iid] = count
        return _top_n(combined, 5)

    top_chats_week = top_chats_period(chats_week)
    top_chats_month = top_chats_period(chats_month)

    top_users_today = _top_n(filter_type(chats_today, ChatType.private), 5)
    top_users_week = _top_n(filter_type(chats_week, ChatType.private), 5)
    top_users_month = _top_n(filter_type(chats_month, ChatType.private), 5)

    # Build document
    doc = Doc(
        Section(
            KeyValue(_("Today"), Code(total_today)),
            KeyValue(_("This week"), Code(total_week)),
            KeyValue(_("This month"), Code(total_month)),
            title=_("AI usage"),
        ),
        Section(Bold(_("Top chats — today")), *_format_top(top_chats_today_list, chat_by_id)),
        Section(Bold(_("Top chats — this week")), *_format_top(top_chats_week, chat_by_id)),
        Section(Bold(_("Top chats — this month")), *_format_top(top_chats_month, chat_by_id)),
        Section(Bold(_("Top users — today")), *_format_top(top_users_today, chat_by_id)),
        Section(Bold(_("Top users — this week")), *_format_top(top_users_week, chat_by_id)),
        Section(Bold(_("Top users — this month")), *_format_top(top_users_month, chat_by_id)),
    )

    await message.reply(str(doc))
