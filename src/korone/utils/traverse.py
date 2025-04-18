# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2022 Victor Cebarros <https://github.com/victorcebarros>

from collections import deque
from collections.abc import Iterable
from typing import Any, TypeVar

T = TypeVar("T")


def bfs_attr_search(root: Any, attr: str) -> Any:
    queue: deque = deque([root])
    visited: set[int] = set()

    while queue:
        obj = queue.popleft()
        obj_id = id(obj)

        if obj_id in visited:
            continue
        visited.add(obj_id)

        if hasattr(obj, attr):
            return getattr(obj, attr)

        try:
            neighbors: Iterable = (
                getattr(obj, name) for name in vars(obj) if not name.startswith("_")
            )
            queue.extend(n for n in neighbors if id(n) not in visited)
        except TypeError:
            continue

    msg = f"Could not find attribute '{attr}' in the object or its attributes"
    raise AttributeError(msg)
