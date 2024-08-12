# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from .api import DeepL
from .errors import QuotaExceededError, TranslationError

__all__ = ("DeepL", "QuotaExceededError", "TranslationError")
