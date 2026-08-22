import asyncio
from dataclasses import dataclass
from hashlib import blake2s
from time import monotonic
from typing import TYPE_CHECKING, Self

from korone.logger import get_logger
from korone.modules.metadata import InlineQueryContribution

if TYPE_CHECKING:
    from collections.abc import Mapping

    from aiogram.types import InlineQuery, InlineQueryResultsButton, InlineQueryResultUnion

    from korone.modules.metadata import LoadedModule, ModuleInlineQuery

MAX_INLINE_RESULTS = 50
MAX_RESULT_ID_BYTES = 64
INLINE_QUERY_TOTAL_TIMEOUT_SECONDS = 6.0

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class RegisteredInlineQueryProvider:
    module_slug: str
    provider: ModuleInlineQuery


@dataclass(frozen=True, slots=True)
class InlineQueryRegistry:
    providers: tuple[RegisteredInlineQueryProvider, ...]

    @classmethod
    def from_modules(cls, modules: Mapping[str, LoadedModule]) -> Self:
        providers = sorted(
            (
                RegisteredInlineQueryProvider(module_slug=slug, provider=module.inline_query)
                for slug, module in modules.items()
                if module.inline_query is not None
            ),
            key=lambda registered: registered.provider.priority,
            reverse=True,
        )

        return cls(providers=tuple(providers))

    async def collect(self, query: InlineQuery) -> tuple[list[InlineQueryResultUnion], InlineQueryResultsButton | None]:
        tasks: list[tuple[RegisteredInlineQueryProvider, asyncio.Task[InlineQueryContribution]]] = []
        try:
            async with asyncio.timeout(INLINE_QUERY_TOTAL_TIMEOUT_SECONDS):
                async with asyncio.TaskGroup() as task_group:
                    for registered in self.providers:
                        task = task_group.create_task(
                            _collect_provider(registered, query), name=f"inline-query:{registered.module_slug}"
                        )
                        tasks.append((registered, task))
        except TimeoutError:
            await logger.awarning(
                "Inline query aggregation timed out", timeout_seconds=INLINE_QUERY_TOTAL_TIMEOUT_SECONDS
            )

        results: list[InlineQueryResultUnion] = []
        seen_result_ids: set[str] = set()
        empty_state_button = None
        for registered, task in tasks:
            if task.cancelled():
                continue
            contribution = task.result()
            if empty_state_button is None and contribution.empty_state_button is not None:
                empty_state_button = contribution.empty_state_button

            for result in contribution.results:
                if not result.id:
                    await logger.awarning(
                        "Inline query provider returned an empty result ID", module=registered.module_slug
                    )
                    continue

                namespaced_result = _namespace_result(registered.module_slug, result)
                if namespaced_result.id in seen_result_ids:
                    await logger.awarning(
                        "Inline query provider returned a duplicate result ID", module=registered.module_slug
                    )
                    continue

                seen_result_ids.add(namespaced_result.id)
                results.append(namespaced_result)
                if len(results) >= MAX_INLINE_RESULTS:
                    break
            if len(results) >= MAX_INLINE_RESULTS:
                break

        available_result_count = sum(len(task.result().results) for _, task in tasks if not task.cancelled())
        if available_result_count > len(results):
            await logger.adebug(
                "Inline query results discarded",
                available_result_count=available_result_count,
                returned_result_count=len(results),
            )

        return results, empty_state_button if not results else None


async def _collect_provider(registered: RegisteredInlineQueryProvider, query: InlineQuery) -> InlineQueryContribution:
    started_at = monotonic()
    try:
        async with asyncio.timeout(registered.provider.timeout_seconds):
            contribution = await registered.provider.collect(query)
    except TimeoutError:
        await logger.awarning(
            "Inline query provider timed out",
            module=registered.module_slug,
            timeout_seconds=registered.provider.timeout_seconds,
        )
        return InlineQueryContribution()
    except Exception as exc:  # ruff: ignore[blind-except]
        await logger.aexception("Inline query provider failed", module=registered.module_slug, error=str(exc))
        return InlineQueryContribution()
    await logger.adebug(
        "Inline query provider completed",
        module=registered.module_slug,
        duration_seconds=monotonic() - started_at,
        result_count=len(contribution.results),
    )
    return contribution


def _namespaced_result_id(module_slug: str, result_id: str) -> str:
    namespaced_id = f"{module_slug}:{result_id}"
    if len(namespaced_id.encode()) <= MAX_RESULT_ID_BYTES:
        return namespaced_id

    digest = blake2s(namespaced_id.encode(), digest_size=16).hexdigest()
    hashed_id = f"{module_slug}:{digest}"
    if len(hashed_id.encode()) <= MAX_RESULT_ID_BYTES:
        return hashed_id
    return digest


def _namespace_result(module_slug: str, result: InlineQueryResultUnion) -> InlineQueryResultUnion:
    return result.model_copy(update={"id": _namespaced_result_id(module_slug, result.id)})
