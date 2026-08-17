# ALGORITHM_SPEC.md

**HCMC Delivery AI Search - Algorithm Specification**

Version: 3.0

Status: **Enforced** (for every search algorithm in `algorithms/`).

This document defines the *shared* contract that every search algorithm follows: the
common interface, the single output model, the shared helpers, and the per-algorithm
requirements. BFS-specific details live in `docs/BFS_SPEC.md`; this file is the
authoritative shared framework and intentionally has no BFS-only content. Project
structure and dependency flow follow `CONVENTION.md § 2`.

---

# 1. Purpose & Scope

Algorithms only implement searching. An algorithm:

* consumes a validated graph (`data.models.GraphData` or `delivery.models.DeliveryGraph`),
* returns exactly one `core.search_result.SearchResult` (re-exported by `algorithms`),
* never loads files, prints, renders UI, or mutates the graph.

It may use the shared helpers in `algorithms/metrics.py` and `algorithms/heuristic.py`.
It must NOT re-implement them.

---

# 2. Supported Algorithms

| # | Algorithm | Module | Owner | Status |
|---|-----------|--------|-------|--------|
| 1 | Breadth-First Search (BFS) | `algorithms/bfs.py` | Hưng | implemented |
| 2 | Depth-First Search (DFS) | `algorithms/dfs.py` | Văn Đức | planned |
| 3 | Uniform Cost Search (UCS) | `algorithms/ucs.py` | Minh Đức | planned |
| 4 | A* | `algorithms/astar.py` | Minh Đức | planned |
| 5 | Dijkstra | `algorithms/dijkstra.py` | Hằng | planned |
| 6 | IDA* | `algorithms/ida_star.py` | Hằng | planned |
| 7 | Multi-location route (Nearest Neighbour/TSP) | `algorithms/` | Văn Đức | planned |
| 8 | Greedy Best-First | `algorithms/` (mock provider, roadmap §10) | Hưng | planned |

Each algorithm is one pure function in its own module (`algorithms/<name>.py`), sharing
the signature pattern below. Adding an algorithm must not require touching the UI, the
backend, or other algorithms. Implementations register their `SearchAlgorithm` subclass
in the core registry (`core.search_algorithm.ALGORITHM_REGISTRY`), so callers can use
`run_algorithm(name, graph, start, goal)` instead of importing the module.

---

# 3. Common Interface

## 3.1 Signature

Algorithms consume graphs through the structural `GraphLike` protocol
(`shared/types.py`), which both `data.models.GraphData` and
`delivery.models.DeliveryGraph` satisfy (each exposes `.nodes`/`.edges`). Algorithms do
not import the concrete graph model, so the same function works on either layer.

```python
from shared.types import GraphLike
from core.search_result import SearchResult

def bfs(graph: GraphLike, start: str, goal: str, enable_logging: bool = True) -> SearchResult: ...
def dfs(graph: GraphLike, start: str, goal: str, enable_logging: bool = True) -> SearchResult: ...
def ucs(graph: GraphLike, start: str, goal: str, enable_logging: bool = True) -> SearchResult: ...
def astar(graph: GraphLike, start: str, goal: str, enable_logging: bool = True) -> SearchResult: ...
# ... same pattern for every algorithm
```

Rules:

* `graph` is a validated `GraphData` or `DeliveryGraph` (both expose `.nodes` and
  `.edges`). Algorithms depend on that shape only.
* `start`/`goal` are node ids (strings) matching `graph` node ids.
* The return type is exactly `SearchResult` — never `None`, a tuple, or a dict.
* `enable_logging=False` must produce the same `path` and `visited_nodes` but `steps=[]`.
* No algorithm writes to the graph; all state is local.

## 3.2 Graph access

Use the small shared helpers instead of re-implementing scans:

* `algorithms.metrics.build_edge_lookup(graph)` → `dict[(start, end), Edge]` for O(1)
  lookups.
* `algorithms.metrics.path_metrics(graph, path, edge_lookup=None)` → `(distance_km, time_min)`.
* `algorithms.metrics.path_total_cost(graph, path, edge_lookup=None, *, cost_fn)` → summed cost.
* `algorithms.metrics.find_edge(graph, start, end)` → `Edge | None` for single lookups.

Never iterate all `graph.edges` inside the hot loop to find neighbors for a node; build
the outgoing-index once (see `delivery.road.RoadGraph` for the pattern).

---

# 4. Output Model (single shared shape)

`core/search_result.py` is authoritative (re-exported by `algorithms`). Every algorithm
fills every field.

```python
class SearchStep(BaseModel):
    current_node: str
    frontier: list[str]
    reason: str


class SearchResult(BaseModel):
    path: list[str]
    visited_nodes: list[str]
    steps: list[SearchStep]
    total_distance_km: float
    total_time_min: float
    total_cost: float
    processing_time_ms: float
    explanation: str
```

### 4.1 Field semantics (algorithm-agnostic)

| Field | Meaning |
|-------|---------|
| `path` | node ids `start → … → goal`, inclusive. `[]` when no path exists. |
| `visited_nodes` | node ids in the exact order they were **expanded** (dequeued/popped). |
| `steps` | one `SearchStep` per expanded node, same order as `visited_nodes`; empty when `enable_logging=False`. |
| `total_distance_km` | sum of `distance_km` along `path`; `0.0` when no path. |
| `total_time_min` | sum of `time_min` along `path`; `0.0` when no path. |
| `total_cost` | sum of the shared edge-cost along `path` (§ 6); `0.0` for a hop-count-only algorithm when no path. |
| `processing_time_ms` | wall-clock duration of the call, in ms. |
| `explanation` | Vietnamese string explaining why this path was chosen. |

### 4.2 SearchStep

Each step records one expansion: the node expanded, the frontier at that moment (ordered),
and a short Vietnamese `reason` for choosing it — enough for the UI to animate.

---

# 5. Input Validation & Failure (all algorithms)

Every algorithm validates before searching:

1. `start` and `goal` exist in `graph.nodes`; if not, return `SearchResult` with `path=[]`
   and an explanatory `explanation` (Vietnamese) listing the missing node(s).
2. `start == goal` returns `path=[start]`, `steps=[]`, zeroed metrics, with an
   explanation that start equals goal.
3. No path found (disconnected / unreachable): return `path=[]` with the visited order
   and an explanation that no route exists.

Algorithms must not raise for the *data-driven* cases above. Genuine bugs (missing edges
on a reconstructed path, malformed graph) raise project exceptions — see
`CONVENTION.md § 6`.

---

# 6. Cost Function (shared)

Owned in `config/defaults.py` (`CostWeights`, `DEFAULT_WEIGHTS`), re-exported by
`algorithms/heuristic.py` where `edge_cost` lives:

```python
from config.defaults import CostWeights, DEFAULT_WEIGHTS

@dataclass(frozen=True, slots=True)
class CostWeights:
    distance: float = 0.3   # α
    time: float = 0.4       # β
    congestion: float = 0.2 # γ
    risk: float = 0.1       # δ


DEFAULT_WEIGHTS = CostWeights()

def edge_cost(edge, weights: CostWeights = DEFAULT_WEIGHTS) -> float: ...
```

Path cost:

```text
Cost = α·Distance + β·Time + γ·Congestion + δ·Risk
```

Rules:

* Weighted algorithms (UCS, A*, Dijkstra, IDA*) use `edge_cost` (or a traffic-adjusted
  variant owned by the cost owner) as their g/f value.
* BFS/DFS ignore weights for *deciding* the path but still report `total_cost` via
  `edge_cost` for comparison.
* Never invent a private cost equation inside an algorithm.

---

# 7. Per-Algorithm Requirements

Each row references the shared contract above; only algorithm-specific expectations are
listed here.

## 7.1 BFS

See `docs/BFS_SPEC.md` (the dedicated, implementation-ready contract). Summary:
FIFO `deque`, expands by hop-distance, fewest-edge path, hop-optimal only.

## 7.2 DFS

* Stack-based (explicit `list` or recursion). Cycle-safe via a visited set.
* Not optimal; complete on finite graphs.
* `explanation` must state DFS depth-first bias and that the found path may be long.

## 7.3 UCS

* `heapq` priority queue keyed on accumulated `g(n)`.
* Uses `edge_cost` (§ 6). Handles equal-cost ties deterministically (e.g. by node id) so
  results are reproducible.
* Optimal when edge costs are non-negative (true for this dataset).

## 7.4 A*

* `f(n) = g(n) + h(n)`, `g` from `edge_cost`, `h` a user-provided admissible heuristic.
* Default heuristic: Haversine distance / max speed (or per-road-class speed) so `h`
  never overestimates `time_min` or `distance_km`.
* Records `h`/`f` in the step `reason` when logging is on.

## 7.5 Dijkstra

* Single-source; returns the shortest path to `goal` (or all reachable when goal is
  `None`-like). Shares code with UCS; kept as a separate exported function.
* Uses `edge_cost` (or distance-only, per the dataset contract). Optimal, non-negative
  edges only.

## 7.6 IDA*

* Iterative deepening on the `f` threshold. Memory-efficient; admissible heuristic
  required for optimality.
* Step `reason` should report bound updates.

## 7.7 Multi-location routing

* Optimizes an ordered visit of multiple POIs (Nearest Neighbour first, then 2-opt etc.).
* Returns a `SearchResult` whose `path` is the concatenated POI route; `explanation`
  describes the order heuristic and its optimality caveat.

---

# 8. Serialization

Every `SearchResult` serializes via Pydantic (`model_dump()`). Field names are exactly
those in `core/search_result.py` and MUST NOT be renamed by the backend or frontend.
Unknown fields in a payload are ignored by consumers.

---

# 9. Testing (all algorithms)

Per `CONVENTION.md § 9`, plus:

* A by-hand trace on a tiny graph asserted exactly (order, frontier, path).
* Missing-node, start==goal, and disconnected cases.
* For weighted algorithms: an example where the cheap path differs from the fewest-hop
  path, proving weights are honored.
* Determinism: run twice, identical result.
* All fixtures annotated; no network/time-dependent behaviour.

---

# 10. Relationship to other docs

* `docs/BFS_SPEC.md` — the BFS-specific contract (this doc's only child).
* `CONVENTION.md` — project layout, typing, exceptions, tests, static analysis.