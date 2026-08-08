# algorithms

One module per algorithm plus the shared cost/metric helpers. The uniform output model
(`SearchResult`, `SearchStep`) and the algorithm registry live in `core/`.

Implemented:

* `bfs.py` -> `bfs(graph, start, goal, enable_logging=True)` -> BFS (fewest hops), also
  registered as `BFSAlgorithm` so `run_algorithm("bfs", ...)` works. Operates on both the
  road graph (`data.GraphData`) and the delivery graph (`delivery.DeliveryGraph`).
* `base.py` -> shared `build_result`, `reconstruct_path`, and the `register_algorithm`
  decorator used by every algorithm module.
* `metrics.py` -> shared path aggregation (`build_edge_lookup`, `path_metrics`,
  `path_total_cost`, `find_edge`). Protocols come from `shared/types.py`.
* `heuristic.py` -> shared `edge_cost`; re-exports `CostWeights` / `DEFAULT_WEIGHTS`
  (owned in `config/defaults.py`).

TODO (other owners): DFS, UCS, A*, Dijkstra, IDA*, Greedy Best-First, and multi-location
routing (`algorithms/dfs.py`, `ucs.py`, `astar.py`, `dijkstra.py`, `ida_star.py` are
placeholders that raise `NotImplementedError`). All share the same signature pattern as
`bfs` and register their `SearchAlgorithm` subclass (`ALGORITHM_SPEC.md § 2-3`).

See `docs/BFS_SPEC.md` for the BFS contract and `ALGORITHM_SPEC.md` for the shared
interface.
