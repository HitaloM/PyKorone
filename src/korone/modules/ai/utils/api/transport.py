from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

import httpx

from korone.logger import get_logger

from .helpers import now_unix, request_id, to_rounded_int
from .openai_compat import (
    adapt_chat_completion_request,
    build_stream_payload,
    extract_error_message_from_payload,
    normalize_completion_response,
    openai_error_response,
)
from .token_manager import VulcanTokenManager

if TYPE_CHECKING:
    from .settings import VulcanAPISettings

logger = get_logger(__name__)


class VulcanOpenAITransport(httpx.AsyncBaseTransport):
    def __init__(self, settings: VulcanAPISettings, *, timeout: float = 60.0) -> None:
        self._settings = settings
        self._upstream_client = httpx.AsyncClient(timeout=httpx.Timeout(timeout), follow_redirects=True)
        self._token_manager = VulcanTokenManager(settings, self._upstream_client)

    async def aclose(self) -> None:
        await self._upstream_client.aclose()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        normalized_path = request.url.path.rstrip("/")
        method = request.method.upper()

        if method == "POST" and normalized_path.endswith("/chat/completions"):
            return await self._handle_chat_completions(request)

        if method == "GET" and normalized_path.endswith("/models"):
            return self._handle_models(request)

        if method == "GET" and "/models/" in normalized_path:
            return self._handle_model(request, normalized_path)

        msg = f"Unsupported OpenAI-compatible endpoint: {request.url.path}"
        return openai_error_response(request, status_code=404, message=msg)

    def _handle_models(self, request: httpx.Request) -> httpx.Response:
        body = {
            "object": "list",
            "data": [
                {"id": self._settings.default_model, "object": "model", "created": now_unix(), "owned_by": "vulcanlabs"}
            ],
        }
        return httpx.Response(status_code=200, json=body, request=request)

    @staticmethod
    def _handle_model(request: httpx.Request, normalized_path: str) -> httpx.Response:
        model_id = normalized_path.rsplit("/", maxsplit=1)[-1]
        body = {"id": model_id, "object": "model", "created": now_unix(), "owned_by": "vulcanlabs"}
        return httpx.Response(status_code=200, json=body, request=request)

    async def _handle_chat_completions(self, request: httpx.Request) -> httpx.Response:
        try:
            request_obj: object = json.loads(await request.aread())
        except json.JSONDecodeError:
            return openai_error_response(request, status_code=400, message="Request body must be valid JSON.")

        if not isinstance(request_obj, dict):
            return openai_error_response(request, status_code=400, message="Request body must be a JSON object.")

        request_payload = cast("dict[str, object]", request_obj)
        stream_requested = bool(request_payload.pop("stream", False))

        request_payload["nsfw_check"] = False
        request_payload["model"] = self._settings.default_model
        request_payload["temperature"] = to_rounded_int(request_payload.get("temperature"), default=1)
        request_payload["top_p"] = to_rounded_int(request_payload.get("top_p"), default=1)

        request_payload = adapt_chat_completion_request(request_payload)
        messages = request_payload.get("messages")
        if not messages:
            return openai_error_response(
                request, status_code=400, message="At least one non-empty message is required."
            )

        try:
            upstream_response = await self._request_chat_completion(request_payload)
        except httpx.HTTPStatusError as exc:
            logger.warning("Vulcan token request failed with status %s", exc.response.status_code)
            return openai_error_response(
                request, status_code=502, message="Could not obtain a valid AI provider token."
            )
        except httpx.HTTPError:
            logger.exception("Vulcan request failed")
            return openai_error_response(
                request, status_code=502, message="Could not reach the configured AI provider."
            )

        if upstream_response.status_code >= 400:
            message = self._extract_upstream_error_message(upstream_response)
            return openai_error_response(request, status_code=upstream_response.status_code, message=message)

        try:
            payload_obj: object = upstream_response.json()
        except json.JSONDecodeError:
            return openai_error_response(
                request, status_code=502, message="AI provider returned an invalid JSON response."
            )

        if not isinstance(payload_obj, dict):
            return openai_error_response(
                request, status_code=502, message="AI provider returned an unexpected response payload."
            )

        payload = cast("dict[str, object]", payload_obj)
        error_message = extract_error_message_from_payload(payload)
        if error_message:
            return openai_error_response(request, status_code=502, message=error_message)

        normalized = normalize_completion_response(payload, requested_model=self._settings.default_model)
        if stream_requested:
            return httpx.Response(
                status_code=200,
                content=build_stream_payload(normalized),
                headers={
                    "Content-Type": "text/event-stream; charset=utf-8",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
                request=request,
            )

        return httpx.Response(
            status_code=200, json=normalized, headers={"Content-Type": "application/json"}, request=request
        )

    async def _request_chat_completion(self, payload: dict[str, object]) -> httpx.Response:
        token = await self._token_manager.get_valid_token()
        response = await self._upstream_client.post(
            self._settings.chat_url, json=payload, headers=self._build_chat_headers(token)
        )

        if response.status_code in {401, 403}:
            self._token_manager.invalidate()
            token = await self._token_manager.get_valid_token()
            response = await self._upstream_client.post(
                self._settings.chat_url, json=payload, headers=self._build_chat_headers(token)
            )

        return response

    def _build_chat_headers(self, token: str) -> dict[str, str]:
        return {
            "X-Auth-Token": self._settings.x_auth_token,
            "Authorization": f"Bearer {token}",
            "X-Vulcan-Application-ID": self._settings.application_id,
            "Accept": "application/json",
            "User-Agent": self._settings.chat_user_agent,
            "X-Vulcan-Request-ID": request_id(self._settings.request_id_prefix),
            "Content-Type": "application/json; charset=utf-8",
        }

    @staticmethod
    def _extract_upstream_error_message(response: httpx.Response) -> str:
        try:
            payload_obj: object = response.json()
        except json.JSONDecodeError:
            return f"AI provider request failed with status {response.status_code}."

        if isinstance(payload_obj, dict):
            payload = cast("dict[str, object]", payload_obj)
            message = extract_error_message_from_payload(payload)
            if message:
                return message

        return f"AI provider request failed with status {response.status_code}."
