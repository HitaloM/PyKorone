# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2022 Victor Cebarros <https://github.com/victorcebarros>

from collections import deque
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable

T = TypeVar("T")


def bfs_attr_search(root: Any, attr: str) -> Any:
    """Search for an attribute in an object and its attributes using breadth-first search.

    This function performs a breadth-first search traversal through the given object and all
    its attributes to find an attribute with the specified name. It avoids infinite recursion
    by tracking visited objects.

    Args:
        root: The root object to start searching from.
        attr: The name of the attribute to search for.

    Returns:
        The value of the first found attribute with the given name.

    Raises:
        AttributeError: If the attribute is not found in the object or any of its attributes.
    """
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
