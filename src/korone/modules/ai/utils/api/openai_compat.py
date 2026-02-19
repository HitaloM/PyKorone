from __future__ import annotations

import json
from uuid import uuid4

import httpx

from .helpers import now_unix, to_rounded_int

_DEFAULT_FUNCTION_ARGUMENTS = "{}"
_FUNCTION_CALL_FINISH_REASON = "function_call"
_TOOL_CALLS_FINISH_REASON = "tool_calls"


def extract_text_content(content: object) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    chunks.append(text)
                continue

            if not isinstance(item, dict):
                continue

            text = item.get("text")
            if isinstance(text, str):
                stripped_text = text.strip()
                if stripped_text:
                    chunks.append(stripped_text)
                continue

            nested_content = item.get("content")
            if isinstance(nested_content, str):
                stripped_text = nested_content.strip()
                if stripped_text:
                    chunks.append(stripped_text)

        return " ".join(chunks).strip()

    if isinstance(content, dict):
        text = content.get("text")
        if isinstance(text, str):
            return text.strip()

    return ""


def _serialize_function_arguments(arguments: object) -> str:
    if isinstance(arguments, str):
        parsed = arguments.strip()
        return parsed or _DEFAULT_FUNCTION_ARGUMENTS

    if isinstance(arguments, (dict, list)):
        return json.dumps(arguments, ensure_ascii=False)

    return _DEFAULT_FUNCTION_ARGUMENTS


def _extract_function_call(raw_function_call: object) -> dict[str, str] | None:
    if not isinstance(raw_function_call, dict):
        return None

    raw_name = raw_function_call.get("name")
    if not isinstance(raw_name, str):
        return None

    function_name = raw_name.strip()
    if not function_name:
        return None

    function_arguments = _serialize_function_arguments(raw_function_call.get("arguments"))
    return {"name": function_name, "arguments": function_arguments}


def _extract_tool_calls(raw_tool_calls: object) -> list[dict[str, str]]:
    if not isinstance(raw_tool_calls, list):
        return []

    normalized_calls: list[dict[str, str]] = []
    for raw_tool_call in raw_tool_calls:
        if not isinstance(raw_tool_call, dict):
            continue

        raw_function = raw_tool_call.get("function")
        function_call = _extract_function_call(raw_function if isinstance(raw_function, dict) else raw_tool_call)
        if function_call is None:
            continue

        tool_call_id = raw_tool_call.get("id")
        normalized_calls.append({
            "id": tool_call_id if isinstance(tool_call_id, str) and tool_call_id else f"call_{uuid4().hex[:24]}",
            "name": function_call["name"],
            "arguments": function_call["arguments"],
        })

    return normalized_calls


def normalize_messages(messages: object) -> list[dict[str, object]]:
    if not isinstance(messages, list):
        return []

    tool_name_by_id: dict[str, str] = {}
    normalized: list[dict[str, object]] = []

    for item in messages:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        if not isinstance(role, str) or not role:
            continue

        text_content = extract_text_content(item.get("content"))
        tool_calls = _extract_tool_calls(item.get("tool_calls"))
        for tool_call in tool_calls:
            tool_name_by_id[tool_call["id"]] = tool_call["name"]

        function_call = _extract_function_call(item.get("function_call"))
        if function_call is None and tool_calls:
            first_call = tool_calls[0]
            function_call = {"name": first_call["name"], "arguments": first_call["arguments"]}

        if role == "assistant" and function_call is not None:
            normalized.append({"role": "assistant", "content": text_content or None, "function_call": function_call})
            continue

        if role == "tool":
            tool_call_id = item.get("tool_call_id")
            raw_name = item.get("name")
            function_name = raw_name.strip() if isinstance(raw_name, str) else None
            if not function_name and isinstance(tool_call_id, str):
                function_name = tool_name_by_id.get(tool_call_id)
            if not function_name:
                continue

            normalized.append({"role": "function", "name": function_name, "content": text_content})
            continue

        if role == "function":
            raw_name = item.get("name")
            function_name = raw_name.strip() if isinstance(raw_name, str) else ""
            if not function_name:
                continue

            normalized.append({"role": "function", "name": function_name, "content": text_content})
            continue

        if not text_content:
            continue

        message: dict[str, object] = {"role": role, "content": text_content}
        raw_name = item.get("name")
        if isinstance(raw_name, str) and raw_name.strip():
            message["name"] = raw_name.strip()
        normalized.append(message)

    return normalized


def _map_tool_choice(tool_choice: object) -> str | dict[str, str] | None:
    if isinstance(tool_choice, str):
        if tool_choice in {"auto", "none"}:
            return tool_choice
        if tool_choice == "required":
            return "auto"
        return None

    if not isinstance(tool_choice, dict):
        return None

    function_payload = tool_choice.get("function")
    if isinstance(function_payload, dict):
        function_name = function_payload.get("name")
        if isinstance(function_name, str) and function_name.strip():
            return {"name": function_name.strip()}

    raw_name = tool_choice.get("name")
    if isinstance(raw_name, str) and raw_name.strip():
        return {"name": raw_name.strip()}

    return None


def _extract_functions_from_tools(raw_tools: object) -> list[dict[str, object]]:
    if not isinstance(raw_tools, list):
        return []

    functions: list[dict[str, object]] = []
    for raw_tool in raw_tools:
        if not isinstance(raw_tool, dict):
            continue
        if raw_tool.get("type") != "function":
            continue

        raw_function = raw_tool.get("function")
        if not isinstance(raw_function, dict):
            continue

        raw_name = raw_function.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            continue

        function_payload: dict[str, object] = {"name": raw_name.strip()}
        raw_description = raw_function.get("description")
        if isinstance(raw_description, str):
            function_payload["description"] = raw_description

        raw_parameters = raw_function.get("parameters")
        if isinstance(raw_parameters, dict):
            function_payload["parameters"] = raw_parameters

        functions.append(function_payload)

    return functions


def adapt_chat_completion_request(payload: dict[str, object]) -> dict[str, object]:
    adapted_payload = dict(payload)
    adapted_payload["messages"] = normalize_messages(adapted_payload.get("messages"))

    raw_tools = adapted_payload.pop("tools", None)
    functions = _extract_functions_from_tools(raw_tools)
    if functions:
        adapted_payload["functions"] = functions

    adapted_payload.pop("parallel_tool_calls", None)
    if "function_call" not in adapted_payload:
        mapped_tool_choice = _map_tool_choice(adapted_payload.pop("tool_choice", None))
        if mapped_tool_choice is not None:
            adapted_payload["function_call"] = mapped_tool_choice
    else:
        adapted_payload.pop("tool_choice", None)

    return adapted_payload


def extract_error_message_from_payload(payload: dict[str, object]) -> str | None:
    raw_error = payload.get("error")
    if isinstance(raw_error, str):
        return raw_error

    if isinstance(raw_error, dict):
        message = raw_error.get("message")
        if isinstance(message, str):
            return message

    return None


def _normalize_tool_call(raw_tool_call: object) -> dict[str, object] | None:
    if not isinstance(raw_tool_call, dict):
        return None

    raw_function = raw_tool_call.get("function")
    function_call = _extract_function_call(raw_function if isinstance(raw_function, dict) else raw_tool_call)
    if function_call is None:
        return None

    raw_id = raw_tool_call.get("id")
    tool_call_id = raw_id if isinstance(raw_id, str) and raw_id else f"call_{uuid4().hex[:24]}"
    return {"id": tool_call_id, "type": "function", "function": function_call}


def _build_openai_tool_calls(raw_message: dict[str, object]) -> list[dict[str, object]] | None:
    raw_tool_calls = raw_message.get("tool_calls")
    if isinstance(raw_tool_calls, list):
        mapped_tool_calls = [tool_call for call in raw_tool_calls if (tool_call := _normalize_tool_call(call))]
        if mapped_tool_calls:
            return mapped_tool_calls

    raw_function_call = raw_message.get("function_call")
    if raw_function_call is None:
        raw_function_call = raw_message.get("FunctionCall")

    function_call = _extract_function_call(raw_function_call)
    if function_call is None:
        return None

    return [{"id": f"call_{uuid4().hex[:24]}", "type": "function", "function": function_call}]


def _extract_raw_message(raw_choice: dict[str, object]) -> dict[str, object] | None:
    raw_message = raw_choice.get("message")
    if not isinstance(raw_message, dict):
        raw_message = raw_choice.get("Message")

    if not isinstance(raw_message, dict):
        return None

    return raw_message


def normalize_completion_response(payload: dict[str, object], *, requested_model: str) -> dict[str, object]:
    model_name = payload.get("model")
    response_model = model_name if isinstance(model_name, str) and model_name else requested_model

    normalized: dict[str, object] = {
        "id": payload.get("id") if isinstance(payload.get("id"), str) else f"chatcmpl-{uuid4().hex}",
        "object": "chat.completion",
        "created": to_rounded_int(payload.get("created"), default=now_unix()),
        "model": response_model,
        "choices": [],
    }

    usage = payload.get("usage")
    if not isinstance(usage, dict):
        usage = payload.get("Usage")
    if isinstance(usage, dict):
        normalized["usage"] = usage

    raw_choices = payload.get("choices")
    if not isinstance(raw_choices, list):
        raw_choices = payload.get("Choices")

    choices: list[dict[str, object]] = []
    if isinstance(raw_choices, list):
        for index, raw_choice in enumerate(raw_choices):
            if not isinstance(raw_choice, dict):
                continue

            raw_message = _extract_raw_message(raw_choice)
            if not isinstance(raw_message, dict):
                continue

            role = raw_message.get("role")
            if not isinstance(role, str):
                role = raw_message.get("Role")
            message_role = role if isinstance(role, str) and role else "assistant"
            raw_content = raw_message.get("content")
            if raw_content is None:
                raw_content = raw_message.get("Content")
            message_content = extract_text_content(raw_content)
            tool_calls = _build_openai_tool_calls(raw_message)

            finish_reason = raw_choice.get("finish_reason")
            finish_reason_text = finish_reason if isinstance(finish_reason, str) and finish_reason else "stop"
            if finish_reason_text == _FUNCTION_CALL_FINISH_REASON:
                finish_reason_text = _TOOL_CALLS_FINISH_REASON
            if tool_calls and finish_reason_text == "stop":
                finish_reason_text = _TOOL_CALLS_FINISH_REASON

            message_payload: dict[str, object] = {"role": message_role}
            if message_content:
                message_payload["content"] = message_content
            elif tool_calls:
                message_payload["content"] = None
            else:
                message_payload["content"] = ""
            if tool_calls:
                message_payload["tool_calls"] = tool_calls

            choice: dict[str, object] = {
                "index": to_rounded_int(raw_choice.get("index"), default=index),
                "message": message_payload,
                "finish_reason": finish_reason_text,
            }

            choices.append(choice)

    normalized["choices"] = choices
    return normalized


def build_stream_payload(chat_completion: dict[str, object]) -> bytes:
    choices = chat_completion.get("choices")
    if not isinstance(choices, list) or not choices:
        return b"data: [DONE]\n\n"

    chunks: list[str] = []
    for raw_choice in choices:
        if not isinstance(raw_choice, dict):
            continue

        message = raw_choice.get("message")
        if not isinstance(message, dict):
            continue

        content = message.get("content")
        content_text = content if isinstance(content, str) else ""
        raw_tool_calls = message.get("tool_calls")

        delta: dict[str, object] = {"role": "assistant"}
        if content_text:
            delta["content"] = content_text
        if isinstance(raw_tool_calls, list) and raw_tool_calls:
            delta["tool_calls"] = raw_tool_calls
        if "content" not in delta and "tool_calls" not in delta:
            delta["content"] = ""

        chunk: dict[str, object] = {
            "id": chat_completion["id"],
            "object": "chat.completion.chunk",
            "created": chat_completion["created"],
            "model": chat_completion["model"],
            "choices": [
                {
                    "index": raw_choice.get("index", 0),
                    "delta": delta,
                    "finish_reason": raw_choice.get("finish_reason", "stop"),
                }
            ],
        }
        chunks.append(f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n")

    chunks.append("data: [DONE]\n\n")
    return "".join(chunks).encode("utf-8")


def openai_error_response(request: httpx.Request, *, status_code: int, message: str) -> httpx.Response:
    body = {"error": {"message": message, "type": "invalid_request_error"}}
    return httpx.Response(status_code=status_code, json=body, request=request)
