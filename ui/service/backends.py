"""Algorithm catalog + real→mock backend dispatch (GUI_ROADMAP § 10 / § 11 / § 13).

Task-025: the service only calls the real algorithm (``core.run_algorithm``);
when the name is missing from the registry it falls back to the matching mock and
returns ``source="mock"``.

Task-026: the real algorithm is loaded **on demand** — ``_discover`` imports
``algorithms.<name>`` so a teammate module's ``@register_algorithm`` side effect
lands in the core registry before the first ``run_algorithm`` call.

Fallback contract (GUI_ROADMAP § 10): the mock is used **only** on a registry
miss — an unimportable module or a module that registers nothing — or when a
**registered placeholder** raises `NotImplementedError` (its explicit "not
ready yet" marker). Any other crash of a registered algorithm (``KeyError``,
``RuntimeError``, …) surfaces as `SEARCH_FAILED` at the HTTP layer — it is
**never** masked by the mock.

The frontend never branches on this — it reads the ``mock`` flag / ``source``
from the catalog and the service (§ 13 ownership: `SearchBackend`/`AlgorithmCatalog`
are internal service types).
"""

from __future__ import annotations

from importlib import import_module

from core.search_algorithm import ALGORITHM_REGISTRY, run_algorithm
from core.search_result import SearchResult
from shared.logger import get_logger

from . import graphs
from .errors import AlgorithmUnavailableError, AlgorithmUnknownError
from .mocks import MockAstar, MockDFS, MockGreedy, MockProvider, MockUCS

__all__ = ["AlgorithmCatalog", "SearchBackend", "run_search"]

logger = get_logger(__name__)


class AlgorithmCatalog:
    """Declarative list of selectable algorithms and their mock status.

    The catalog is the single authoritative list of algorithm names the UI can
    pick; ``mock`` marks whether today's build backs that algorithm with a mock
    provider rather than a real teammate module.
    """

    def __init__(self) -> None:
        self._entries: dict[str, dict[str, bool | str]] = {
            "bfs": {"label": "Breadth-First Search", "mock": False},
            "dfs": {"label": "Depth-First Search", "mock": True},
            "ucs": {"label": "Uniform-Cost Search", "mock": True},
            "greedy": {"label": "Greedy Best-First Search", "mock": True},
            "astar": {"label": "A* Search", "mock": True},
        }

    def names(self) -> list[str]:
        return list(self._entries)

    def has(self, name: str) -> bool:
        return name in self._entries

    def is_mock(self, name: str) -> bool:
        return bool(self._entries.get(name, {}).get("mock", False))

    def label(self, name: str) -> str:
        entry = self._entries.get(name)
        return str(entry["label"]) if entry else name

    def all(self) -> list[dict[str, bool | str]]:
        return [
            {"id": name, "label": entry["label"], "mock": entry["mock"]}
            for name, entry in self._entries.items()
        ]


# Provider class per catalog name for the fallback path.
_MOCK_PROVIDERS: dict[str, type[MockProvider]] = {
    "dfs": MockDFS,
    "ucs": MockUCS,
    "greedy": MockGreedy,
    "astar": MockAstar,
}


def _discover(name: str) -> None:
    """Import ``algorithms.<name>`` on demand so a teammate module registers.

    Task-026: a teammate ships ``algorithms/<name>.py`` whose module-level
    ``@register_algorithm`` decorator populates the core registry; importing the
    module IS the discovery step. Discovery never changes the fallback contract:
    a module that exists but registers nothing its class is still a registry
    miss and falls through to the mock (or an unknown-name error).
    """
    if name in ALGORITHM_REGISTRY:
        return
    try:
        import_module(f"algorithms.{name}")
    except ImportError:
        logger.debug("no teammate module algorithms.%s; using mock fallback", name)


class SearchBackend:
    """Runs a search, selecting between the real algorithm and its mock.

    Encapsulates the `discover → registry-miss → mock, else → real` rule so
    ``/search`` is a thin HTTP shell and the strategy is unit-testable in
    isolation. ``source`` is ``"real"`` when the registered algorithm produced
    the result and ``"mock"`` when the fallback provider did. A registered
    placeholder that raises `NotImplementedError` also falls back to the mock
    (GUI_ROADMAP § 10); only a missing registry entry with no mock surfaces as
    an explicit error.
    """

    def __init__(self, catalog: AlgorithmCatalog | None = None) -> None:
        self.catalog = catalog or AlgorithmCatalog()

    def run(
        self,
        name: str,
        start: str,
        goal: str,
        *,
        enable_logging: bool = True,
    ) -> tuple[SearchResult, str]:
        """Return ``(result, source)``; ``source`` is ``"real"`` or ``"mock"``.

        Uses the mock when discovery left ``name`` unregistered, or when a
        registered placeholder raises `NotImplementedError` (GUI_ROADMAP § 10).
        A registered algorithm that crashes on a real bug (``KeyError``,
        ``RuntimeError``, …) is **never** masked — its exception propagates.

        Raises:
            AlgorithmUnknownError: when ``name`` has no registered algorithm and
                no mock fallback.
            AlgorithmUnavailableError: when a registered placeholder has no
                mock fallback (§ 7: real path raises and no mock exists).
            Other exceptions: propagated from a registered algorithm (never
                masked by the mock).
        """
        delivery_graph = graphs.get_delivery_graph()
        _discover(name)

        if name not in ALGORITHM_REGISTRY:
            logger.debug("no real %r ready, trying mock fallback", name)
            provider_cls = _MOCK_PROVIDERS.get(name)
            if provider_cls is None:
                raise AlgorithmUnknownError(
                    f"No registered algorithm or mock named {name!r}; "
                    f"available: {sorted(self.catalog.names())}"
                )
            result = provider_cls().search(
                delivery_graph,
                start,
                goal,
                enable_logging=enable_logging,
            )
            return result, "mock"

        logger.debug("running registered algorithm %s %s -> %s", name, start, goal)
        try:
            result = run_algorithm(
                name,
                delivery_graph,
                start,
                goal,
                enable_logging=enable_logging,
            )
        except NotImplementedError as exc:
            # A registered placeholder: `NotImplementedError` is its explicit
            # "not ready yet" marker (§ 10 fallback). Fall back to the matching
            # mock so the UI can still demo; only fail (409, § 7) when there is
            # no mock to fall back to.
            logger.debug("registered %r is a placeholder; trying mock fallback", name)
            provider_cls = _MOCK_PROVIDERS.get(name)
            if provider_cls is None:
                raise AlgorithmUnavailableError(
                    f"The registered algorithm {name!r} raised "
                    "NotImplementedError and no mock is available."
                ) from exc
            result = provider_cls().search(
                delivery_graph,
                start,
                goal,
                enable_logging=enable_logging,
            )
            return result, "mock"
        return result, "real"


# Module-level shared backend (process-lifetime like the graph cache).
_BACKEND = SearchBackend()


def run_search(
    name: str,
    start: str,
    goal: str,
    *,
    enable_logging: bool = True,
) -> tuple[SearchResult, str]:
    """Module-level facade for ``/search``; delegates to the shared backend."""
    return _BACKEND.run(name, start, goal, enable_logging=enable_logging)