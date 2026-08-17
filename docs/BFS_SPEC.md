# BFS_SPEC.md

**HCMC Delivery AI Search - Breadth-First Search (BFS) Specification**

Version: 2.0

Owner: Hưng

Status: **Authoritative** (for the BFS implementation in `algorithms/bfs.py`).

This document is the BFS-specific contract. The shared algorithm framework (signature,
output model, validation rules, cost function, testing) lives in `ALGORITHM_SPEC.md`; this
file adds only what is unique to BFS and references the shared rules rather than repeating
them.

---

# 1. Purpose

Implement BFS as a pure function that explores a directed graph level by level and returns
exactly one `SearchResult`. BFS finds the **fewest-edge** (fewest-hop) path. Because edges
have differing positive costs, BFS is **not** cost/distance/time-optimal — this is the
central teaching point.

The function is declared in `ALGORITHM_SPEC.md § 3`:

```python
def bfs(graph, start: str, goal: str, enable_logging: bool = True) -> SearchResult: ...
```

It lives at `algorithms/bfs.py` (module-level `bfs()` wrapping the registered
`BFSAlgorithm`) and accepts either the road graph (`data.models.GraphData`)
or the delivery graph (`delivery.models.DeliveryGraph`) — both expose `.nodes` / `.edges`
in the same shape. In practice the UI runs BFS on the **delivery** graph.

---

# 2. Algorithm (reference contract)

Steps:

1. Validate `start` / `goal` exist in `graph.nodes`; if either is missing, return
   `SearchResult(path=[], visited=[], steps=[], explanation=...)` naming the missing node(s).
2. `start == goal` → return `path=[start]`, `steps=[]`, zeroed metrics.
3. Use `collections.deque` FIFO, a `discovered` set, and a `parent` map.
4. On dequeue of node `n`: record it in `visited_nodes` (in expansion order) and, when
   `enable_logging`, append a `SearchStep` (node, current frontier, Vietnamese `reason`).
   For each neighbor `Edge.start == n`, if undiscovered, mark discovered, set parent,
   enqueue.
5. Stop when the goal is dequeued (first time = fewest hops).
6. Reconstruct `path` by walking parents from `goal` back to `start`, then reverse.
7. Compute path metrics + `total_cost` via the shared helpers (`ALGORITHM_SPEC.md § 3.2`,
   § 6).
8. Return the `SearchResult`.

Neighbor lookup: iterate `graph.edges` where `edge.start == current` is acceptable on the
delivery graph (≤ 70 edges). On the road graph, prefer an outgoing index
(`delivery.road.RoadGraph.outgoing()`).

Complexity: time `O(V + E)`, space `O(V)`. Complete on finite graphs; optimal **only by hop
count**.

---

# 3. BFS-specific field semantics

| `SearchResult` field | BFS meaning |
|----------------------|-------------|
| `path` | fewest-hop node-id path `start → … → goal`, inclusive; `[]` if no path. |
| `visited_nodes` | node ids in exact **dequeue (expansion)** order. |
| `steps` | one `SearchStep` per expanded node, same order as `visited_nodes`; `[]` when `enable_logging=False`. |
| `total_distance_km` | sum of `distance_km` along `path`. |
| `total_time_min` | sum of `time_min` along `path`. |
| `total_cost` | sum of shared `edge_cost` along `path` — **reporting only**, BFS ignores weights when choosing. |
| `processing_time_ms` | wall-clock duration of the call. |
| `explanation` | Vietnamese, see § 5. |

Each `SearchStep`:

```python
class SearchStep(BaseModel):
    current_node: str
    frontier: list[str]
    reason: str
```

* `frontier` = ordered queue at the moment of expansion (discovered but not yet expanded).
* `reason` example:

  ```text
  "Duyệt theo BFS (FIFO): lấy node sớm nhất trong hàng đợi (lớp hiện tại)."
  ```

---

# 4. Optimality & completeness (for the report)

| Property | BFS |
|----------|-----|
| Complete | Yes (finite graph) |
| Optimal (hops) | Yes |
| Optimal (cost / dist / time) | **No** |
| Time | O(V + E) |
| Space | O(V) |
| Uses edge weights | No (weight-agnostic) |

BFS expands breadth-first, so the first time the goal is dequeued it is by fewest hops —
not cheapest. Equal-hop alternatives are returned in encounter order without cost
comparison. This is the key limitation to explain in the report.

---

# 5. Explanation requirement (Vietnamese)

`explanation` must follow assignment §4.8, in Vietnamese. Template:

```text
BFS chọn đường đi {path} vì tập trung vào số lượng chặng (ít bước nhất), không phụ thuộc
vào chi phí hay độ dài. Do đó đường này có thể không tối ưu về tổng chi phí/thời gian so
với UCS/A* nếu có đoạn kẹt xe.
```

Include: hop-optimality, explicit non-optimality by cost/time, any high-congestion segment,
and (when the dataset provides one) a short comparison to an alternative route.

---

# 6. Testing (BFS-specific)

`tests/algorithms/test_bfs.py` exists and is green. Requirements:

- [ ] `path[0] == start` and `path[-1] == goal` when a path exists.
- [ ] Consecutive path ids have a real directed edge.
- [ ] Disconnected pair → `path=[]` with a clear `explanation`.
- [ ] `start == goal` → `path=[start]`, `steps=[]`.
- [ ] `len(steps) == len(visited_nodes)` and order identical.
- [ ] `frontier` in each step equals the current queue.
- [ ] Tiny hand-built graph matches a by-hand trace (asserted exactly).
- [ ] `total_cost` matches `edge_cost` sums; `processing_time_ms > 0`.
- [ ] Deterministic: two runs → identical result.

---

# 7. Relationship to other docs

- `ALGORITHM_SPEC.md` — shared signature, output model, validation, cost function.
- `docs/DATASET_SPEC.md` / `docs/DELIVERY_GRAPH.md` — graph inputs.
- `backend/app/schemas.py` — how `SearchResult` and the expanded route are served.