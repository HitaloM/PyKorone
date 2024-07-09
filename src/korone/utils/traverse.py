# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2022 Victor Cebarros <https://github.com/victorcebarros>

from typing import Any


def bfs_attr_search(root: Any, attr: str) -> Any:
    queue: list[Any] = [root]
    visited: list[Any] = [id(root)]
    while queue:
        obj = queue.pop()

        if hasattr(obj, attr):
            return getattr(obj, attr)

        try:
            objs = (getattr(obj, attr) for attr in (s for s in vars(obj) if not s.startswith("_")))
        except TypeError:
            continue

        for neighbor in objs:
            if id(neighbor) not in visited:
                queue.append(neighbor)
                visited.append(id(neighbor))

    msg = f"Could not find attribute {attr}"
    raise AttributeError(msg)
