# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PhoneSearchResult:
    name: str
    url: str
