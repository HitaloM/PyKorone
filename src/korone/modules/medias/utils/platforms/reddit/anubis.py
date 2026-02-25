from __future__ import annotations

import asyncio
import hashlib
import html
import re
from time import perf_counter
from typing import ClassVar
from urllib.parse import parse_qs, urljoin, urlparse

import aiohttp
import orjson

from korone.logger import get_logger

from .constants import ANUBIS_PASS_CHALLENGE_PATH, REDLIB_REQUEST_COOKIES
from .types import _AnubisChallengeInfo

logger = get_logger(__name__)


class RedlibAnubisBypassMixin:
    _json_script_regex_template: ClassVar[str]
    _meta_refresh_regex: ClassVar[re.Pattern[str]]
    _DEFAULT_TIMEOUT: ClassVar[aiohttp.ClientTimeout]

    @staticmethod
    def _coerce_int(value: object) -> int | None:
        msg = "_coerce_int must be implemented by the provider class"
        raise NotImplementedError(msg)

    @classmethod
    def _looks_like_block_page(cls, html_content: str) -> bool:
        msg = "_looks_like_block_page must be implemented by the provider class"
        raise NotImplementedError(msg)

    @classmethod
    async def _solve_anubis_challenge(
        cls, session: aiohttp.ClientSession, *, challenge_html: str, challenge_url: str, headers: dict[str, str]
    ) -> dict[str, str] | None:
        info = cls._extract_anubis_challenge_info(challenge_html, challenge_url)
        if not info:
            return None

        params: dict[str, str]
        if info.algorithm == "metarefresh":
            await asyncio.sleep((max(info.difficulty, 0) * 0.8) + 0.1)
            params = {"id": info.challenge_id, "challenge": info.random_data, "redir": info.redir}
        elif info.algorithm == "preact":
            await asyncio.sleep((max(info.difficulty, 0) * 0.125) + 0.05)
            result = hashlib.sha256(info.random_data.encode("utf-8")).hexdigest()
            params = {"id": info.challenge_id, "result": result, "redir": info.redir}
        elif info.algorithm in {"fast", "slow"}:
            started_at = perf_counter()
            solved = await asyncio.to_thread(cls._solve_pow_challenge, info.random_data, info.difficulty)
            if not solved:
                await logger.adebug(
                    "[Reddit] Anubis PoW challenge not solved",
                    url=challenge_url,
                    algorithm=info.algorithm,
                    difficulty=info.difficulty,
                )
                return None

            response_hash, nonce = solved
            elapsed_time = max(1, int((perf_counter() - started_at) * 1000))
            params = {
                "id": info.challenge_id,
                "response": response_hash,
                "nonce": str(nonce),
                "redir": info.redir,
                "elapsedTime": str(elapsed_time),
            }
        else:
            await logger.adebug("[Reddit] Unsupported Anubis challenge", algorithm=info.algorithm, url=challenge_url)
            return None

        try:
            async with session.get(
                info.pass_url,
                headers=headers,
                cookies=REDLIB_REQUEST_COOKIES,
                params=params,
                allow_redirects=True,
                timeout=cls._DEFAULT_TIMEOUT,
            ) as response:
                if response.status != 200:
                    await logger.adebug(
                        "[Reddit] Failed to pass Anubis challenge",
                        status=response.status,
                        url=info.pass_url,
                        algorithm=info.algorithm,
                    )
                    return None

                html_content = await response.text()
                if cls._looks_like_block_page(html_content):
                    await logger.adebug(
                        "[Reddit] Anubis challenge solved but page still blocked",
                        url=info.pass_url,
                        algorithm=info.algorithm,
                    )
                    return None

                return {"html": html_content, "base_url": str(response.url)}
        except aiohttp.ClientError as exc:
            await logger.aerror("[Reddit] Failed during Anubis challenge solve", error=str(exc), url=info.pass_url)
            return None

    @classmethod
    def _extract_anubis_challenge_info(cls, html_content: str, challenge_url: str) -> _AnubisChallengeInfo | None:
        anubis_payload = cls._extract_json_script(html_content, "anubis_challenge")
        if isinstance(anubis_payload, dict):
            rules = anubis_payload.get("rules")
            challenge = anubis_payload.get("challenge")
            if isinstance(rules, dict) and isinstance(challenge, dict):
                algorithm = str(rules.get("algorithm") or challenge.get("method") or "").strip().lower()
                challenge_id = str(challenge.get("id") or "").strip()
                random_data = str(challenge.get("randomData") or "").strip()
                difficulty = cls._coerce_int(rules.get("difficulty"))
                if difficulty is None:
                    difficulty = cls._coerce_int(challenge.get("difficulty"))
                difficulty = max(difficulty or 0, 0)

                if algorithm and challenge_id and random_data:
                    base_prefix = cls._extract_json_script(html_content, "anubis_base_prefix")
                    prefix = base_prefix if isinstance(base_prefix, str) else ""
                    pass_url = cls._extract_meta_refresh_pass_url(html_content, challenge_url)
                    if not pass_url:
                        pass_url = cls._build_anubis_pass_url(challenge_url, prefix)
                    redir = cls._extract_query_param(pass_url, "redir") or cls._build_challenge_redir(challenge_url)
                    return _AnubisChallengeInfo(
                        algorithm=algorithm,
                        difficulty=difficulty,
                        challenge_id=challenge_id,
                        random_data=random_data,
                        pass_url=pass_url,
                        redir=redir,
                    )

        preact_payload = cls._extract_json_script(html_content, "preact_info")
        if isinstance(preact_payload, dict):
            pass_url_raw = str(preact_payload.get("redir") or "").strip()
            random_data = str(preact_payload.get("challenge") or "").strip()
            difficulty = max(cls._coerce_int(preact_payload.get("difficulty")) or 0, 0)
            if pass_url_raw and random_data:
                pass_url = urljoin(challenge_url, pass_url_raw)
                challenge_id = cls._extract_query_param(pass_url, "id")
                redir = cls._extract_query_param(pass_url, "redir") or cls._build_challenge_redir(challenge_url)
                if challenge_id:
                    return _AnubisChallengeInfo(
                        algorithm="preact",
                        difficulty=difficulty,
                        challenge_id=challenge_id,
                        random_data=random_data,
                        pass_url=pass_url,
                        redir=redir,
                    )

        return None

    @classmethod
    def _extract_json_script(cls, html_content: str, script_id: str) -> object | None:
        pattern = cls._json_script_regex_template.format(script_id=re.escape(script_id))
        match = re.search(pattern, html_content)
        if not match:
            return None

        payload = html.unescape(match.group(1).strip())
        if not payload:
            return None

        try:
            return orjson.loads(payload)
        except orjson.JSONDecodeError:
            return None

    @classmethod
    def _extract_meta_refresh_pass_url(cls, html_content: str, challenge_url: str) -> str:
        match = cls._meta_refresh_regex.search(html_content)
        if not match:
            return ""

        content = html.unescape(match.group(1))
        url_match = re.search(r"(?i)\burl\s*=\s*(.+)$", content)
        if not url_match:
            return ""

        target = url_match.group(1).strip()
        if not target:
            return ""
        return urljoin(challenge_url, target)

    @staticmethod
    def _build_anubis_pass_url(challenge_url: str, base_prefix: str) -> str:
        prefix = base_prefix.strip()
        if prefix and not prefix.startswith("/"):
            prefix = f"/{prefix}"
        prefix = prefix.rstrip("/")
        return urljoin(challenge_url, f"{prefix}{ANUBIS_PASS_CHALLENGE_PATH}")

    @staticmethod
    def _extract_query_param(url: str, key: str) -> str:
        values = parse_qs(urlparse(url).query).get(key)
        if not values:
            return ""
        value = values[0]
        if not isinstance(value, str):
            return ""
        return value.strip()

    @staticmethod
    def _build_challenge_redir(challenge_url: str) -> str:
        parsed = urlparse(challenge_url)
        path = parsed.path or "/"
        if parsed.query:
            return f"{path}?{parsed.query}"
        return path

    @classmethod
    def _solve_pow_challenge(cls, random_data: str, difficulty: int) -> tuple[str, int] | None:
        if difficulty < 0:
            return None

        target_prefix = "0" * difficulty
        started_at = perf_counter()
        nonce = 0

        while perf_counter() - started_at <= 20.0:
            digest = hashlib.sha256(f"{random_data}{nonce}".encode()).hexdigest()
            if digest.startswith(target_prefix):
                return digest, nonce
            nonce += 1

        return None
