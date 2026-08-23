import asyncio
import hashlib
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import StrEnum
from time import perf_counter
from typing import TYPE_CHECKING, Any, ClassVar, override

import sentry_sdk
from aiogram.fsm.storage.redis import RedisEventIsolation
from redis.asyncio.lock import Lock
from redis.exceptions import LockError, LockNotOwnedError, RedisError

from korone.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from aiogram.fsm.storage.base import KeyBuilder, StorageKey
    from redis.asyncio import Redis
    from redis.commands.core import AsyncScript

logger = get_logger(__name__)

_REDIS_SAMPLE_INTERVAL_SECONDS = 5.0


class LockReleaseResult(StrEnum):
    RELEASED = "released"
    MISSING = "missing"
    TOKEN_MISMATCH = "token_mismatch"
    INVALID_RESPONSE = "invalid_response"


@dataclass(frozen=True, slots=True)
class RedisRuntimeSnapshot:
    run_id: str | None
    uptime_seconds: int | None
    expired_keys: int | None
    evicted_keys: int | None
    delete_calls: int | None
    flushdb_calls: int | None
    flushall_calls: int | None
    sampled_at: float

    def as_context(self, *, now: float) -> dict[str, str | int | float | None]:
        return {
            "run_id": self.run_id,
            "uptime_seconds": self.uptime_seconds,
            "expired_keys": self.expired_keys,
            "evicted_keys": self.evicted_keys,
            "delete_calls": self.delete_calls,
            "flushdb_calls": self.flushdb_calls,
            "flushall_calls": self.flushall_calls,
            "sample_age_seconds": round(max(now - self.sampled_at, 0.0), 3),
        }


@dataclass(frozen=True, slots=True)
class LockReleaseDiagnostic:
    result: LockReleaseResult
    ttl_ms: int | None


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _command_calls(command_stats: dict[str, Any], command: str) -> int | None:
    details = command_stats.get(f"cmdstat_{command}")
    if not isinstance(details, dict):
        return None
    return _optional_int(details.get("calls"))


class RedisRuntimeSampler:
    def __init__(
        self, redis: Redis, *, database: int, interval_seconds: float = _REDIS_SAMPLE_INTERVAL_SECONDS
    ) -> None:
        self._redis = redis
        self._database = database
        self._interval_seconds = interval_seconds
        self._snapshot: RedisRuntimeSnapshot | None = None
        self._last_error_type: str | None = None
        self._task: asyncio.Task[None] | None = None

    @property
    def snapshot(self) -> RedisRuntimeSnapshot | None:
        return self._snapshot

    @property
    def last_error_type(self) -> str | None:
        return self._last_error_type

    async def start(self) -> None:
        if self._task is not None:
            return

        await self.refresh()
        await self._log_runtime_audit()
        self._task = asyncio.create_task(self._sample_loop(), name="redis-fsm-runtime-sampler")

    async def close(self) -> None:
        task = self._task
        self._task = None
        if task is None:
            return

        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    async def refresh(self) -> RedisRuntimeSnapshot | None:
        try:
            server = await self._redis.info("server")
            stats = await self._redis.info("stats")
            command_stats = await self._redis.info("commandstats")
        except RedisError as error:
            error_type = type(error).__name__
            if error_type != self._last_error_type:
                await logger.awarning("Redis FSM runtime sampling failed", error_type=error_type)
            self._last_error_type = error_type
            return self._snapshot

        recovered_from = self._last_error_type
        self._last_error_type = None
        snapshot = RedisRuntimeSnapshot(
            run_id=server.get("run_id") if isinstance(server.get("run_id"), str) else None,
            uptime_seconds=_optional_int(server.get("uptime_in_seconds")),
            expired_keys=_optional_int(stats.get("expired_keys")),
            evicted_keys=_optional_int(stats.get("evicted_keys")),
            delete_calls=_command_calls(command_stats, "del"),
            flushdb_calls=_command_calls(command_stats, "flushdb"),
            flushall_calls=_command_calls(command_stats, "flushall"),
            sampled_at=perf_counter(),
        )
        self._snapshot = snapshot
        if recovered_from is not None:
            await logger.ainfo("Redis FSM runtime sampling recovered", previous_error_type=recovered_from)
        return snapshot

    async def _sample_loop(self) -> None:
        while True:
            await asyncio.sleep(self._interval_seconds)
            await self.refresh()

    async def _log_runtime_audit(self) -> None:
        try:
            config = await self._redis.config_get("maxmemory", "maxmemory-policy", "appendonly", "save", "databases")
            persistence = await self._redis.info("persistence")
            clients = await self._redis.info("clients")
            client_list = await self._redis.client_list()
        except RedisError as error:
            await logger.awarning("Redis FSM runtime audit unavailable", error_type=type(error).__name__)
            return

        snapshot = self._snapshot
        database_clients = [client for client in client_list if _optional_int(client.get("db")) == self._database]
        bot_client_names = {
            name
            for client in database_clients
            if isinstance(name := client.get("name"), str) and name.startswith("korone-fsm:")
        }
        bot_clients = sum(
            isinstance(name := client.get("name"), str) and name.startswith("korone-fsm:")
            for client in database_clients
        )
        unnamed_database_clients = sum(not client.get("name") for client in database_clients)
        other_named_database_clients = len(database_clients) - bot_clients - unnamed_database_clients
        await logger.ainfo(
            "Redis FSM runtime audited",
            run_id=snapshot.run_id if snapshot else None,
            uptime_seconds=snapshot.uptime_seconds if snapshot else None,
            expired_keys=snapshot.expired_keys if snapshot else None,
            evicted_keys=snapshot.evicted_keys if snapshot else None,
            delete_calls=snapshot.delete_calls if snapshot else None,
            flushdb_calls=snapshot.flushdb_calls if snapshot else None,
            flushall_calls=snapshot.flushall_calls if snapshot else None,
            maxmemory=config.get("maxmemory"),
            maxmemory_policy=config.get("maxmemory-policy"),
            appendonly=config.get("appendonly"),
            save=config.get("save"),
            configured_databases=config.get("databases"),
            aof_enabled=persistence.get("aof_enabled"),
            loading=persistence.get("loading"),
            rdb_last_bgsave_status=persistence.get("rdb_last_bgsave_status"),
            connected_clients=clients.get("connected_clients"),
            fsm_database_clients=len(database_clients),
            fsm_bot_clients=bot_clients,
            fsm_bot_instances=len(bot_client_names),
            fsm_database_unnamed_clients=unnamed_database_clients,
            fsm_database_other_named_clients=other_named_database_clients,
        )


class DiagnosticRedisLock(Lock):
    _DIAGNOSTIC_RELEASE_SCRIPT: ClassVar[str] = """
        local token = redis.call('get', KEYS[1])
        if not token then
            return {0, -2}
        end
        local ttl = redis.call('pttl', KEYS[1])
        if token ~= ARGV[1] then
            return {-1, ttl}
        end
        redis.call('del', KEYS[1])
        return {1, ttl}
    """
    _lua_diagnostic_release: ClassVar[AsyncScript | None] = None

    def __init__(
        self,
        redis: Redis,
        name: str | bytes | memoryview,
        *,
        timeout: float | None = None,
        sleep: float = 0.1,
        blocking: bool = True,
        blocking_timeout: float | None = None,
        thread_local: bool = True,
        raise_on_release_error: bool = True,
    ) -> None:
        self.release_diagnostic: LockReleaseDiagnostic | None = None
        super().__init__(
            redis=redis,
            name=name,
            timeout=timeout,
            sleep=sleep,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
            thread_local=thread_local,
            raise_on_release_error=raise_on_release_error,
        )

    @override
    def register_scripts(self) -> None:
        super().register_scripts()
        cls = type(self)
        if cls._lua_diagnostic_release is None:
            cls._lua_diagnostic_release = self.redis.register_script(self._DIAGNOSTIC_RELEASE_SCRIPT)

    @override
    async def do_release(self, expected_token: bytes) -> None:
        script = type(self)._lua_diagnostic_release
        if script is None:
            msg = "Diagnostic Redis lock release script is not registered"
            raise LockError(msg)

        response = await script(keys=[self.name], args=[expected_token], client=self.redis)
        if not isinstance(response, list) or len(response) != 2:
            self.release_diagnostic = LockReleaseDiagnostic(LockReleaseResult.INVALID_RESPONSE, None)
            msg = "Diagnostic Redis lock release returned an invalid response"
            raise LockError(msg)

        status = _optional_int(response[0])
        ttl_ms = _optional_int(response[1])
        if status == 1:
            self.release_diagnostic = LockReleaseDiagnostic(LockReleaseResult.RELEASED, ttl_ms)
            return
        if status == 0:
            result = LockReleaseResult.MISSING
        elif status == -1:
            result = LockReleaseResult.TOKEN_MISMATCH
        else:
            result = LockReleaseResult.INVALID_RESPONSE

        self.release_diagnostic = LockReleaseDiagnostic(result, ttl_ms)
        msg = "Cannot release a lock that's no longer owned"
        raise LockNotOwnedError(msg)


class ObservableRedisEventIsolation(RedisEventIsolation):
    def __init__(
        self,
        redis: Redis,
        *,
        runtime_sampler: RedisRuntimeSampler,
        key_builder: KeyBuilder | None = None,
        lock_kwargs: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(redis=redis, key_builder=key_builder, lock_kwargs=lock_kwargs)
        self._runtime_sampler = runtime_sampler

    async def start(self) -> None:
        await self._runtime_sampler.start()

    @override
    async def close(self) -> None:
        await self._runtime_sampler.close()

    @asynccontextmanager
    @override
    async def lock(self, key: StorageKey) -> AsyncGenerator[None]:
        redis_key = self.key_builder.build(key, "lock")
        key_hash = hashlib.sha256(redis_key.encode()).hexdigest()[:16]
        lock = self.redis.lock(name=redis_key, **self.lock_kwargs, lock_class=DiagnosticRedisLock)
        if not isinstance(lock, DiagnosticRedisLock):
            msg = "Redis client did not create the requested diagnostic lock"
            raise LockError(msg)

        acquire_started_at = perf_counter()
        acquired = await lock.acquire()
        acquired_at = perf_counter()
        if not acquired:
            msg = "Blocking FSM lock acquisition returned without ownership"
            raise LockError(msg)

        snapshot_before = self._runtime_sampler.snapshot
        initial_pttl_ms = await self._read_pttl(redis_key)
        try:
            yield None
        finally:
            held_seconds = perf_counter() - acquired_at
            try:
                await lock.release()
            except LockNotOwnedError:
                snapshot_after = await self._runtime_sampler.refresh()
                diagnostic = lock.release_diagnostic or LockReleaseDiagnostic(LockReleaseResult.INVALID_RESPONSE, None)
                context = self._build_failure_context(
                    key_hash=key_hash,
                    lock=lock,
                    acquire_wait_seconds=acquired_at - acquire_started_at,
                    held_seconds=held_seconds,
                    initial_pttl_ms=initial_pttl_ms,
                    diagnostic=diagnostic,
                    snapshot_before=snapshot_before,
                    snapshot_after=snapshot_after,
                )
                sentry_sdk.set_tag("korone.fsm_lock_result", diagnostic.result.value)
                sentry_sdk.set_tag("korone.fsm_lock_hypothesis", str(context["hypothesis"]))
                sentry_sdk.set_context("fsm_lock", context)
                await logger.aerror("Redis FSM event isolation ownership lost", **context)
                raise

    async def _read_pttl(self, redis_key: str) -> int | None:
        try:
            return await self.redis.pttl(redis_key)
        except RedisError as error:
            await logger.awarning(
                "Redis FSM lock initial TTL unavailable",
                key_hash=hashlib.sha256(redis_key.encode()).hexdigest()[:16],
                error_type=type(error).__name__,
            )
            return None

    def _build_failure_context(
        self,
        *,
        key_hash: str,
        lock: DiagnosticRedisLock,
        acquire_wait_seconds: float,
        held_seconds: float,
        initial_pttl_ms: int | None,
        diagnostic: LockReleaseDiagnostic,
        snapshot_before: RedisRuntimeSnapshot | None,
        snapshot_after: RedisRuntimeSnapshot | None,
    ) -> dict[str, object]:
        now = perf_counter()
        run_id_changed = bool(
            snapshot_before
            and snapshot_after
            and snapshot_before.run_id
            and snapshot_after.run_id
            and snapshot_before.run_id != snapshot_after.run_id
        )
        uptime_decreased = bool(
            snapshot_before
            and snapshot_after
            and snapshot_before.uptime_seconds is not None
            and snapshot_after.uptime_seconds is not None
            and snapshot_after.uptime_seconds < snapshot_before.uptime_seconds
        )
        evicted_keys_delta = self._counter_delta(snapshot_before, snapshot_after, "evicted_keys")
        expired_keys_delta = self._counter_delta(snapshot_before, snapshot_after, "expired_keys")
        delete_calls_delta = self._counter_delta(snapshot_before, snapshot_after, "delete_calls")
        flushdb_calls_delta = self._counter_delta(snapshot_before, snapshot_after, "flushdb_calls")
        flushall_calls_delta = self._counter_delta(snapshot_before, snapshot_after, "flushall_calls")
        timeout_seconds = float(lock.timeout) if lock.timeout is not None else None
        hypothesis = self._classify_failure(
            result=diagnostic.result,
            held_seconds=held_seconds,
            timeout_seconds=timeout_seconds,
            run_id_changed=run_id_changed,
            uptime_decreased=uptime_decreased,
            evicted_keys_delta=evicted_keys_delta,
            flushdb_calls_delta=flushdb_calls_delta,
            flushall_calls_delta=flushall_calls_delta,
        )
        return {
            "key_hash": key_hash,
            "release_result": diagnostic.result.value,
            "hypothesis": hypothesis,
            "acquire_wait_seconds": round(acquire_wait_seconds, 3),
            "held_seconds": round(held_seconds, 3),
            "timeout_seconds": timeout_seconds,
            "initial_pttl_ms": initial_pttl_ms,
            "release_pttl_ms": diagnostic.ttl_ms,
            "run_id_changed": run_id_changed,
            "uptime_decreased": uptime_decreased,
            "evicted_keys_delta": evicted_keys_delta,
            "expired_keys_delta": expired_keys_delta,
            "delete_calls_delta": delete_calls_delta,
            "flushdb_calls_delta": flushdb_calls_delta,
            "flushall_calls_delta": flushall_calls_delta,
            "redis_sampling_error": self._runtime_sampler.last_error_type,
            "redis_before": snapshot_before.as_context(now=now) if snapshot_before else None,
            "redis_after": snapshot_after.as_context(now=now) if snapshot_after else None,
        }

    @staticmethod
    def _counter_delta(
        before: RedisRuntimeSnapshot | None, after: RedisRuntimeSnapshot | None, field: str
    ) -> int | None:
        if before is None or after is None:
            return None
        before_value = getattr(before, field)
        after_value = getattr(after, field)
        if before_value is None or after_value is None or after_value < before_value:
            return None
        return after_value - before_value

    @staticmethod
    def _classify_failure(
        *,
        result: LockReleaseResult,
        held_seconds: float,
        timeout_seconds: float | None,
        run_id_changed: bool,
        uptime_decreased: bool,
        evicted_keys_delta: int | None,
        flushdb_calls_delta: int | None,
        flushall_calls_delta: int | None,
    ) -> str:
        if result is LockReleaseResult.TOKEN_MISMATCH:
            return "token_replaced"
        if run_id_changed or uptime_decreased:
            return "redis_restarted"
        if timeout_seconds is not None and held_seconds >= timeout_seconds:
            return "lease_expired"
        if (flushdb_calls_delta is not None and flushdb_calls_delta > 0) or (
            flushall_calls_delta is not None and flushall_calls_delta > 0
        ):
            return "redis_flush_activity"
        if evicted_keys_delta is not None and evicted_keys_delta > 0:
            return "redis_eviction_activity"
        if result is LockReleaseResult.MISSING:
            return "external_delete_restart_or_early_expiry"
        return "undetermined"
