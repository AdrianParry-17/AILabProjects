"""Core search framework: reusable, algorithm-agnostic search scaffolding.

The generic search framework that `algorithms/` builds on. It owns the uniform
`SearchResult` model, the algorithm contract + registry (`SearchAlgorithm`,
`run_algorithm`), event/history/metrics helpers, and depends only on `shared/`.

It never imports `data`, `delivery`, `algorithms`, `visualization`, or `ui`
(ARCHITECTURE.md § 3 dependency flow).
"""

from core.search_algorithm import (
    ALGORITHM_REGISTRY,
    SearchAlgorithm,
    register_algorithm,
    run_algorithm,
)
from core.search_event import SearchEvent, SearchEventKind
from core.search_history import SearchHistory, SearchRun
from core.search_metrics import SearchMetrics
from core.search_result import SearchResult, SearchStep

__all__ = [
    "ALGORITHM_REGISTRY",
    "SearchAlgorithm",
    "SearchEvent",
    "SearchEventKind",
    "SearchHistory",
    "SearchMetrics",
    "SearchResult",
    "SearchRun",
    "SearchStep",
    "register_algorithm",
    "run_algorithm",
]
