"""Search algorithms, one module per algorithm (plus shared helpers).

Public entry points:
    bfs(graph, start, goal, enable_logging=True) -> SearchResult
    run_algorithm("bfs", graph, start, goal) -> SearchResult   # framework registry
    edge_cost, CostWeights, DEFAULT_WEIGHTS                    # cost model

Ownership: `bfs.py` (BFS), `dfs.py`, `ucs.py`, `astar.py`, `dijkstra.py`,
`ida_star.py` are owned by their respective teammates. `base.py` holds the shared
helpers, `heuristic.py` the cost model, `metrics.py` the edge aggregation.
"""

from algorithms.bfs import bfs
from algorithms.heuristic import DEFAULT_WEIGHTS, CostWeights, edge_cost
from core.search_algorithm import ALGORITHM_REGISTRY, run_algorithm
from core.search_result import SearchResult, SearchStep

__all__ = [
    "ALGORITHM_REGISTRY",
    "DEFAULT_WEIGHTS",
    "CostWeights",
    "SearchResult",
    "SearchStep",
    "bfs",
    "edge_cost",
    "run_algorithm",
]
