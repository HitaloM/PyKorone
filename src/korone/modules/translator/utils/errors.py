# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>


class TranslationError(Exception):
    pass


class QuotaExceededError(TranslationError):
    pass
