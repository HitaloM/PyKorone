# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2022 Victor Cebarros <https://github.com/victorcebarros>

from collections import deque
from typing import Any


def bfs_attr_search(root: Any, attr: str) -> Any:
    queue = deque([root])
    visited = set()

    while queue:
        obj = queue.popleft()

        if id(obj) in visited:
            continue
        visited.add(id(obj))

        if hasattr(obj, attr):
            return getattr(obj, attr)

        try:
            neighbors = (getattr(obj, a) for a in vars(obj) if not a.startswith("_"))
        except TypeError:
            continue

        for neighbor in neighbors:
            if id(neighbor) not in visited:
                queue.append(neighbor)

    msg = f"Could not find attribute '{attr}' in the object or its attributes"
    raise AttributeError(msg)
