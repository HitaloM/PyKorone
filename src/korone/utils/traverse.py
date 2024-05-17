# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2022 Victor Cebarros <https://github.com/victorcebarros>

from typing import Any


def bfs_attr_search(root: Any, attr: str) -> Any:
    """
    Perform a breadth-first search (BFS) for an attribute in an object.

    The function performs a breadth-first search (BFS) on an object and its attributes,
    searching for a specific attribute with the given name. The search is done
    iteratively, exploring all the attributes of the objects in a breadth-first order,
    until the desired attribute is found or all objects have been traversed without finding it.

    Parameters
    ----------
    root : Any
        Root of search.
    attr : str
        Attribute name to search.

    Returns
    -------
    Any
        The attribute with name attr found in search.

    Raises
    ------
    AttributeError
        When could not find the attribute.

    Examples
    --------
    >>> def fun():
    ...     pass
    >>> fun.hello = lambda x: x * 2
    >>> fun.hello.again = lambda x: x / 4
    >>> fun.hallo = lambda x: x - 7
    >>> fun.hallo.wieder = lambda x: x**3
    >>> fun.hola = lambda x: x + 2
    >>> fun.hola.otravez = lambda x: x * 8
    >>> bfs_attr_search(fun, "again")
    <function <lambda> at ???>
    >>> bfs_attr_search(fun, "again")(20)
    5.0
    """
    queue: list[Any] = []
    visited: list[Any] = []

    queue.append(root)
    visited.append(id(root))

    while queue:
        obj = queue.pop()

        if hasattr(obj, attr):
            return getattr(obj, attr)

        try:
            objs = (
                getattr(obj, attr) for attr in filter(lambda s: not s.startswith("_"), vars(obj))
            )
        except TypeError:
            continue

        for neighbor in objs:
            if id(neighbor) not in visited:
                queue.append(neighbor)
                visited.append(id(neighbor))

    msg = f"Could not find attribute {attr}"
    raise AttributeError(msg)
