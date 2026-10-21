import asyncio
import hashlib
import html
import re
from threading import Event
from time import perf_counter
from urllib.parse import parse_qs, urljoin, urlparse

import orjson
from argon2.low_level import Type, hash_secret_raw

from korone.logger import get_logger
from korone.modules.medias.parsing import coerce_int

from .constants import ANUBIS_PASS_CHALLENGE_PATH, JSON_SCRIPT_REGEX_TEMPLATE, META_REFRESH_REGEX
from .models import _AnubisChallengeInfo

logger = get_logger(__name__)


async def solve_challenge_parameters(info: _AnubisChallengeInfo, challenge_url: str) -> dict[str, str] | None:
    if info.algorithm == "metarefresh":
        await asyncio.sleep((max(info.difficulty, 0) * 0.8) + 0.1)
        return {"id": info.challenge_id, "challenge": info.random_data, "redir": info.redir}
    if info.algorithm == "preact":
        await asyncio.sleep((max(info.difficulty, 0) * 0.125) + 0.05)
        result = hashlib.sha256(info.random_data.encode("utf-8")).hexdigest()
        return {"id": info.challenge_id, "result": result, "redir": info.redir}
    if info.algorithm not in {"fast", "slow", "argon2id"}:
        await logger.adebug("[Reddit] Unsupported Anubis challenge", algorithm=info.algorithm, url=challenge_url)
        return None

    started_at = perf_counter()
    stop = Event()
    worker = asyncio.create_task(asyncio.to_thread(_solve_pow_challenge, info, stop))
    try:
        solved = await asyncio.shield(worker)
    finally:
        stop.set()
        # Join the worker before releasing the client's calculation slot, including cancellation.
        while not worker.done():
            try:
                await asyncio.shield(worker)
            except asyncio.CancelledError:
                continue
    if not solved:
        await logger.adebug(
            "[Reddit] Anubis PoW challenge not solved",
            url=challenge_url,
            algorithm=info.algorithm,
            difficulty=info.difficulty,
        )
        return None

    response_hash, nonce = solved
    return {
        "id": info.challenge_id,
        "response": response_hash,
        "nonce": str(nonce),
        "redir": info.redir,
        "elapsedTime": str(max(1, int((perf_counter() - started_at) * 1000))),
    }


def extract_challenge_info(html_content: str, challenge_url: str) -> _AnubisChallengeInfo | None:
    anubis_payload = _extract_json_script(html_content, "anubis_challenge")
    if isinstance(anubis_payload, dict):
        info = _extract_anubis_payload(anubis_payload, html_content, challenge_url)
        if info is not None:
            return info

    preact_payload = _extract_json_script(html_content, "preact_info")
    return _extract_preact_payload(preact_payload, challenge_url) if isinstance(preact_payload, dict) else None


def _extract_anubis_payload(
    payload: dict[object, object], html_content: str, challenge_url: str
) -> _AnubisChallengeInfo | None:
    rules = payload.get("rules")
    challenge = payload.get("challenge")
    if not isinstance(rules, dict) or not isinstance(challenge, dict):
        return None

    algorithm = str(rules.get("algorithm") or challenge.get("method") or "").strip().lower()
    challenge_id = str(challenge.get("id") or "").strip()
    random_data = str(challenge.get("randomData") or "").strip()
    difficulty = coerce_int(rules.get("difficulty"))
    if difficulty is None:
        difficulty = coerce_int(challenge.get("difficulty"))
    difficulty = max(difficulty or 0, 0)
    if not algorithm or not challenge_id or not random_data:
        return None

    base_prefix = _extract_json_script(html_content, "anubis_base_prefix")
    prefix = base_prefix if isinstance(base_prefix, str) else ""
    pass_url = _extract_meta_refresh_pass_url(html_content, challenge_url) or _build_pass_url(challenge_url, prefix)
    redir = _extract_query_param(pass_url, "redir") or _build_challenge_redir(challenge_url)
    return _AnubisChallengeInfo(
        algorithm=algorithm,
        difficulty=difficulty,
        challenge_id=challenge_id,
        random_data=random_data,
        pass_url=pass_url,
        redir=redir,
    )


def _extract_preact_payload(payload: dict[object, object], challenge_url: str) -> _AnubisChallengeInfo | None:
    pass_url_raw = str(payload.get("redir") or "").strip()
    random_data = str(payload.get("challenge") or "").strip()
    if not pass_url_raw or not random_data:
        return None

    pass_url = urljoin(challenge_url, pass_url_raw)
    challenge_id = _extract_query_param(pass_url, "id")
    if not challenge_id:
        return None

    return _AnubisChallengeInfo(
        algorithm="preact",
        difficulty=max(coerce_int(payload.get("difficulty")) or 0, 0),
        challenge_id=challenge_id,
        random_data=random_data,
        pass_url=pass_url,
        redir=_extract_query_param(pass_url, "redir") or _build_challenge_redir(challenge_url),
    )


def _extract_json_script(html_content: str, script_id: str) -> object | None:
    pattern = JSON_SCRIPT_REGEX_TEMPLATE.format(script_id=re.escape(script_id))
    match = re.search(pattern, html_content)
    if not match or not (payload := html.unescape(match.group(1).strip())):
        return None
    try:
        return orjson.loads(payload)
    except orjson.JSONDecodeError:
        return None


def _extract_meta_refresh_pass_url(html_content: str, challenge_url: str) -> str:
    match = META_REFRESH_REGEX.search(html_content)
    if not match:
        return ""
    url_match = re.search(r"(?i)\burl\s*=\s*(.+)$", html.unescape(match.group(1)))
    return urljoin(challenge_url, url_match.group(1).strip()) if url_match and url_match.group(1).strip() else ""


def _build_pass_url(challenge_url: str, base_prefix: str) -> str:
    prefix = base_prefix.strip()
    if prefix and not prefix.startswith("/"):
        prefix = f"/{prefix}"
    return urljoin(challenge_url, f"{prefix.rstrip('/')}{ANUBIS_PASS_CHALLENGE_PATH}")


def _extract_query_param(url: str, key: str) -> str:
    values = parse_qs(urlparse(url).query).get(key)
    return values[0].strip() if values and isinstance(values[0], str) else ""


def _build_challenge_redir(challenge_url: str) -> str:
    parsed = urlparse(challenge_url)
    path = parsed.path or "/"
    return f"{path}?{parsed.query}" if parsed.query else path


def _solve_pow_challenge(info: _AnubisChallengeInfo, stop: Event) -> tuple[str, int] | None:
    if info.difficulty < 0:
        return None
    if info.algorithm == "argon2id":
        if info.difficulty > 256:
            return None
        try:
            challenge = bytes.fromhex(info.random_data)
        except ValueError:
            return None
        if not challenge or len(challenge) > 4096:
            return None
    else:
        if info.difficulty > 64:
            return None
        challenge = b""

    started_at = perf_counter()
    nonce = 0
    while not stop.is_set() and perf_counter() - started_at < 20.0:
        if info.algorithm == "argon2id":
            # Anubis v1.28.1 uses RustCrypto Argon2::default(), raw challenge bytes,
            # and a u64 nonce salt whose byte order depends on the last challenge byte.
            salt = nonce.to_bytes(8, "little" if challenge[-1] >= 128 else "big")
            digest = hash_secret_raw(
                challenge, salt, time_cost=2, memory_cost=19456, parallelism=1, hash_len=32, type=Type.ID, version=19
            )
            valid = int.from_bytes(digest, "big") >> (256 - info.difficulty) == 0
        else:
            digest = hashlib.sha256(f"{info.random_data}{nonce}".encode()).digest()
            valid = digest.hex().startswith("0" * info.difficulty)
        if valid:
            return digest.hex(), nonce
        nonce += 1
    return None
