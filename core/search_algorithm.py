"""The reusable search framework: algorithm contract + registry.

Every concrete algorithm (BFS today; DFS/UCS/A*/Dijkstra/IDA* by their owners) is a
`SearchAlgorithm` subclass registered under its `name`. The UI/visualization/report
layers only need `run_algorithm(name, graph, start, goal)` — they never import a
specific algorithm module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.search_result import SearchResult
from shared.types import GraphLike


class SearchAlgorithm(ABC):
    """Contract implemented by every search algorithm in `algorithms/`."""

    name: str = "base"

    @abstractmethod
    def search(
        self,
        graph: GraphLike,
        start: str,
        goal: str,
        **kwargs: object,
    ) -> SearchResult:
        """Run the algorithm and return a uniform `SearchResult`."""

    def run(
        self,
        graph: GraphLike,
        start: str,
        goal: str,
        **kwargs: object,
    ) -> SearchResult:
        """Alias of `search` for callers that prefer `run` semantics."""
        return self.search(graph, start, goal, **kwargs)


ALGORITHM_REGISTRY: dict[str, type[SearchAlgorithm]] = {}


def register_algorithm(algorithm_class: type[SearchAlgorithm]) -> type[SearchAlgorithm]:
    """Class decorator that registers an algorithm under its `name`."""
    ALGORITHM_REGISTRY[algorithm_class.name] = algorithm_class
    return algorithm_class


def run_algorithm(
    name: str,
    graph: GraphLike,
    start: str,
    goal: str,
    **kwargs: object,
) -> SearchResult:
    """Run the registered algorithm `name` and return its `SearchResult`.

    Raises:
        KeyError: when no algorithm named `name` is registered.
    """
    try:
        algorithm_class = ALGORITHM_REGISTRY[name]
    except KeyError as exc:
        raise KeyError(
            f"No registered algorithm {name!r}; available: {sorted(ALGORITHM_REGISTRY)}"
        ) from exc
    return algorithm_class().search(graph, start, goal, **kwargs)
