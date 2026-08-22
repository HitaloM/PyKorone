import asyncio
from dataclasses import dataclass
from hashlib import blake2s
from typing import TYPE_CHECKING

from korone.logger import get_logger
from korone.modules.metadata import InlineQueryContribution

if TYPE_CHECKING:
    from collections.abc import Mapping

    from aiogram.types import InlineQuery, InlineQueryResultsButton, InlineQueryResultUnion

    from korone.modules.metadata import LoadedModule, ModuleInlineQuery

MAX_INLINE_RESULTS = 50
MAX_RESULT_ID_BYTES = 64

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class RegisteredInlineQueryProvider:
    module_slug: str
    provider: ModuleInlineQuery


INLINE_QUERY_PROVIDERS: list[RegisteredInlineQueryProvider] = []


def configure_inline_query_providers(modules: Mapping[str, LoadedModule]) -> None:
    INLINE_QUERY_PROVIDERS.clear()
    INLINE_QUERY_PROVIDERS.extend(
        RegisteredInlineQueryProvider(module_slug=slug, provider=module.inline_query)
        for slug, module in modules.items()
        if module.inline_query is not None
    )


async def _collect_provider(registered: RegisteredInlineQueryProvider, query: InlineQuery) -> InlineQueryContribution:
    try:
        return await registered.provider.collect(query)
    except Exception as exc:  # ruff: ignore[blind-except]
        await logger.aexception("Inline query provider failed", module=registered.module_slug, error=str(exc))
        return InlineQueryContribution()


def _namespaced_result_id(module_slug: str, result_id: str) -> str:
    namespaced_id = f"{module_slug}:{result_id}"
    if len(namespaced_id.encode()) <= MAX_RESULT_ID_BYTES:
        return namespaced_id
    return blake2s(namespaced_id.encode(), digest_size=16).hexdigest()


def _namespace_result(module_slug: str, result: InlineQueryResultUnion) -> InlineQueryResultUnion:
    return result.model_copy(update={"id": _namespaced_result_id(module_slug, result.id)})


async def collect_inline_query_results(
    query: InlineQuery,
) -> tuple[list[InlineQueryResultUnion], InlineQueryResultsButton | None]:
    tasks: list[tuple[RegisteredInlineQueryProvider, asyncio.Task[InlineQueryContribution]]] = []
    async with asyncio.TaskGroup() as task_group:
        for registered in INLINE_QUERY_PROVIDERS:
            task = task_group.create_task(
                _collect_provider(registered, query), name=f"inline-query:{registered.module_slug}"
            )
            tasks.append((registered, task))

    results: list[InlineQueryResultUnion] = []
    empty_state_button = None
    for registered, task in tasks:
        contribution = task.result()
        if empty_state_button is None and contribution.button is not None:
            empty_state_button = contribution.button
        results.extend(
            _namespace_result(registered.module_slug, result)
            for result in contribution.results[: MAX_INLINE_RESULTS - len(results)]
        )
        if len(results) >= MAX_INLINE_RESULTS:
            break

    return results, empty_state_button if not results else None
