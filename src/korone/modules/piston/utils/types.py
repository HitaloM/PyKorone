# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunRequest:
    language: str
    code: str | None = None
    stdin: str | None = None

    def to_dict(self) -> dict:
        return {
            "language": self.language,
            "version": "*",
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
