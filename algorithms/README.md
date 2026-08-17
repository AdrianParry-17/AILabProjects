# algorithms

One module per algorithm plus the shared cost/metric helpers. The uniform output model
(`SearchResult`, `SearchStep`) and the algorithm registry live in `core/`.

Implemented:

* `bfs.py` -> `bfs(graph, start, goal, enable_logging=True)` -> BFS (fewest hops), also
  registered as `BFSAlgorithm` so `run_algorithm("bfs", ...)` works. Operates on both the
  road graph (`data.GraphData`) and the delivery graph (`delivery.DeliveryGraph`).
* `ucs.py` -> `ucs(graph, start, goal, enable_logging=True)` -> uniform-cost search
  (minimum weighted cost), registered as `UCSAlgorithm`. Uses a `heapq` frontier with
  deterministic tie-breaking; its `straight_line_heuristic` returns 0 for admissibility.
* `astar.py` -> `astar(graph, start, goal, enable_logging=True)` -> A* search, registered
  as `AStarAlgorithm`. Uses the admissible `straight_line_heuristic`
  (`weights.distance * haversine_km`) so it never overestimates the remaining cost.
* `base.py` -> shared `build_result`, `reconstruct_path`, and the `register_algorithm`
  decorator used by every algorithm module.
* `metrics.py` -> shared path aggregation (`build_edge_lookup`, `path_metrics`,
  `path_total_cost`, `find_edge`). Protocols come from `shared/types.py`.
* `heuristic.py` -> shared `edge_cost`, `straight_line_heuristic` / `haversine_km`
  helpers; re-exports `CostWeights` / `DEFAULT_WEIGHTS` (owned in `config/defaults.py`).

Entry points (`algorithms/__init__.py`): `bfs`, `ucs`, `astar`, `edge_cost`, plus
`run_algorithm("bfs"|"ucs"|"astar", ...)`.

TODO (other owners): DFS, Dijkstra, IDA*, Greedy Best-First, and multi-location routing
(`algorithms/dfs.py`, `dijkstra.py`, `ida_star.py` are placeholders that raise
`NotImplementedError`). All share the same signature pattern as `bfs` and register their
`SearchAlgorithm` subclass (`ALGORITHM_SPEC.md § 2-3`).

See `docs/BFS_SPEC.md` for the BFS contract and `ALGORITHM_SPEC.md` for the shared
interface.
