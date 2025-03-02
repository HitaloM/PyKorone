# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from cashews import Cache

cache = Cache()
cache.setup("redis://localhost", client_side=True)
