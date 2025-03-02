# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunRequest:
    language: str
    code: str
    stdin: str | None = None
    version: str = "*"

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "version": self.version,
            "files": self.code,
            "stdin": self.stdin or "",
        }


@dataclass(frozen=True, slots=True)
class RunResponse:
    result: str
    output: str | None = None
    compiler_output: str | None = None

    @staticmethod
    def from_api_response(data: dict) -> RunResponse:
        return RunResponse(
            result="success",
            output=data.get("run", {}).get("output", None),
            compiler_output=data.get("compile", {}).get("output", None),
        )
