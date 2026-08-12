# Algorithm & Heuristic Reference

Tài liệu này mô tả đúng implementation hiện tại của backend, không chỉ mô tả textbook. Ký hiệu:

- `V`, `E`: số node và directed edge traversable;
- `b`: branching factor;
- `d`: độ sâu goal nông nhất/theo lời giải đang xét;
- `g(n)`: accumulated weighted route cost;
- `h(n)`: estimated remaining weighted cost;
- `f(n)=g(n)+h(n)`;
- mọi edge đóng hoặc `traversable=false` không thuộc graph khả dụng của run.

## 1. Unified search contract

Mọi thuật toán được gọi qua:

```text
run_algorithm(graph, cost, heuristics, algorithm, heuristic,
              start, goal, SearchOptions)
```

và trả cùng `SearchResult`:

```text
algorithm, heuristic, start_id, goal_id, status, found,
path, edge_ids, total_cost, metrics, trace_events, trace_truncated
```

Invariant khi found:

- `path[0] == start_id`, `path[-1] == goal_id`;
- `len(edge_ids) == len(path)-1`;
- edge `edge_ids[i]` nối có hướng `path[i] -> path[i+1]`;
- `total_cost == Σ edge_cost(edge_ids[i])`;
- API `metrics.path_cost == cost_breakdown.total_cost`.

Status:

| Status | Meaning |
|---|---|
| `found` | goal đã được tìm và path reconstruct thành công |
| `unreachable` | frontier hết mà không có route traversable |
| `limit_reached` | dừng trước khi có route do chạm `max_expansions` |

Trường hợp `start==goal` trả path một node, không edge, cost 0 và GeoJSON LineString gồm hai coordinate giống nhau để hợp lệ về cấu trúc.

## 2. Summary comparison

| ID | Selection rule | Weighted cost aware? | Uses `h`? | Complete* | Optimality* | Typical time | Space |
|---|---|---:|---:|---:|---|---|---|
| `bfs` | FIFO / shallowest | chỉ để báo metric, không để chọn | no | yes | minimum hops only | `O(V+E)` | `O(V)` |
| `dfs` | LIFO / deepest | chỉ để báo metric, không để chọn | no | yes | no | `O(V+E)` | `O(V)` incl. discovered |
| `ucs` | smallest `g` | yes | no | yes | yes for non-negative cost | `O((V+E)log V)` | `O(V+E)` heap worst case |
| `dijkstra` | smallest settled distance | yes | no | yes | yes for non-negative cost | `O((V+E)log V)` | `O(V+E)` heap worst case |
| `astar` | smallest `g+h` | yes | yes | yes | admissible/consistent `h` | graph-search commonly `O((V+E)log V)`, AI worst case exponential | frontier/labels up to `O(V+E)` |
| `greedy_best_first` | smallest `h` | no for selection | yes | yes on finite graph | no | `O((V+E)log V)` | `O(V)` plus heap |
| `bidirectional_dijkstra` | min label from either end | yes | no | yes | yes for non-negative cost | worst `O((V+E)log V)` | `O(V+E)` |
| `ida_star` | DFS under repeated `f` bounds | yes | yes | conditional | admissible `h` + positive finite edge costs | often `O(b^d)`, may re-expand heavily | `O(d)` recursion/path, excluding trace storage |

\* Claims assume a finite graph and no operational expansion cap. `max_expansions` can turn any long run into `limit_reached`. Complexity excludes HTTP, explanation/alternative generation and UI animation. With `include_trace=true`, stored trace adds up to `max_trace_events` records.

## 3. Breadth-First Search — `bfs`

### Principle

BFS stores `(node, depth)` in a FIFO `deque`. It marks a node discovered when enqueued and records the first parent edge. It therefore explores nondecreasing hop depth.

```text
queue = [start]
while queue:
    n = pop_left()
    if n == goal: reconstruct
    for each traversable outgoing edge n->c:
        if c undiscovered: discover, parent[c]=n, append_right(c)
```

### Properties

- Complete on a finite graph because every reachable node is discovered at most once.
- Optimal only in number of edges/hops, or in cost when every edge cost is identical.
- Not guaranteed to minimize distance, ETA, risk or composite cost.
- Deterministic because graph adjacency order and enqueue order are deterministic.

### Trace

Emits `start`, `expand`, `discover`, `finish`. `g_cost` in trace is computed for the chosen first-parent path for explanation; it does not affect FIFO ordering.

## 4. Depth-First Search — `dfs`

### Principle

DFS uses a Python list as LIFO stack. Neighbor candidates are iterated in reverse before pushing so the earliest adjacency item is explored first after the pop.

### Properties

- Complete on this finite graph implementation because `discovered` is global and each reachable node is pushed at most once.
- Not optimal in hops or weighted cost.
- Route quality is highly sensitive to adjacency/tie order.
- `O(V+E)` traversal, `O(V)` discovered/parent/stack memory; the theoretical recursive DFS `O(depth)` memory claim would omit the global discovered table and is not the implementation here.

### Trace

Emits the same event family as BFS; `depth` makes the “go deep, then backtrack” behavior visible.

## 5. Uniform-Cost Search — `ucs`

### Principle

UCS uses a min-heap keyed by accumulated cost `g`. A relaxation replaces `distance[child]` and parent only when candidate is strictly better (with `1e-12` tolerance). A node becomes settled on its first non-stale pop.

### Properties

- Complete on this finite graph; textbook infinite-tree completeness additionally assumes edge cost bounded away from zero.
- Optimal for non-negative edge costs. The cost model satisfies non-negativity for traversable edges.
- Binary heap implementation has conventional `O((V+E)log V)` time; stale entries may remain until popped.
- No heuristic calls.

### Trace

Uses `relax`, not `discover`, because the same node label can improve before settlement. `f_cost` equals `g_cost`.

## 6. Dijkstra — `dijkstra`

The API exposes Dijkstra separately for teaching and comparison, but pair routing maps both `ucs` and `dijkstra` to the same `_uniform_cost` implementation. On this graph model they therefore have identical frontier policy and route guarantee. Tiny runtime differences between labeled runs are measurement noise, not algorithmic differences.

Dijkstra is also the trusted primitive for:

- every directed pair in multi-stop matrix construction;
- every single-edge-exclusion alternative candidate;
- exact weighted baseline comparisons.

## 7. A* Search — `astar`

### Principle

A* orders a min-heap by `f=g+h`, stores best known `g`, and records parents on better relaxations. `closed_best[node]` stores the best expanded `g`; a node may be reopened if a strictly better `g` later arrives. The run stops when the goal is popped as the current best candidate.

### Properties

- With `zero`, A* degenerates to UCS/Dijkstra.
- With `haversine` or `travel_time`, `h` is admissible and consistent for the implemented cost, so the first popped goal is optimal.
- With `traffic_aware`, `h` can overestimate; route may be faster to find but the optimality guarantee is removed.
- A stronger safe heuristic can reduce expansions but its computation also costs CPU. “Fewer expanded nodes” does not imply lower measured milliseconds on every small run.

### Trace

`start`, `expand` and `relax` carry `g_cost`, `h_cost`, `f_cost`. `heuristic_calls` counts calls made by the search.

## 8. Greedy Best-First Search — `greedy_best_first`

### Principle

Greedy orders only by `h`, ignoring `g` in selection. It still accumulates cost along its first-parent path for the returned metrics. Nodes are globally marked when discovered, so it does not reconsider a cheaper later path.

### Properties

- Complete on the finite traversable graph unless expansion cap intervenes.
- Not optimal; a locally promising direction can lead to a large detour.
- May expand very few nodes when heuristic aligns with the road network.
- `traffic_aware` can be pragmatically directed but has no correctness guarantee.

An individual test where Greedy equals Dijkstra optimum is a result for that input, not a theorem.

## 9. Bidirectional Dijkstra — `bidirectional_dijkstra`

### Principle

Two Dijkstra waves run simultaneously:

- forward from start through outgoing edges;
- backward from goal through **incoming** edges, essential for a directed graph.

The implementation expands the side with smaller current minimum label. Whenever a node has labels from both directions, it updates the best meeting cost. It stops safely when:

```text
min_forward + min_backward >= best_meeting_cost
```

Forward parents and backward next-edge links reconstruct one correctly oriented route.

### Properties

- Complete and optimal for non-negative edge cost.
- Can reduce explored search radius in favorable graphs, but does not guarantee fewer expansions than one-way Dijkstra. Asymmetric direction/topology and frontier shape matter.
- Requires both outgoing and incoming adjacency indexes.

### Trace

Events include `direction: "forward"` or `"backward"`. The UI can distinguish the two waves even though they share one event stream.

## 10. Iterative Deepening A* — `ida_star`

### Principle

IDA* begins with threshold `h(start)` and runs depth-first search restricted to `f<=threshold`. A pruned node returns its `f`; the next iteration uses the smallest exceeded `f` as the new threshold. `on_path` prevents a cycle within the current recursion path.

```text
threshold = h(start)
repeat:
    result, next_threshold = depth_first_f_bound(start, threshold)
    if found: return path
    threshold = next_threshold
```

### Properties and caveats

- Memory for active path is `O(d)`; however enabled trace storage is additional bounded memory.
- Repeats expansions across thresholds, sometimes dramatically.
- Optimal with admissible heuristic under the usual positive finite edge-cost conditions.
- Completeness/termination claim is conditional on those costs and no expansion cap. An unusual request that makes some traversable edge cost zero weakens the textbook IDA* condition.
- On the bundled long-distance graph, `max_expansions=100000` can be reached before a solution; this is an expected operational limitation, not permission to report “unreachable.” Status must be read as `limit_reached`.

### Trace

Adds `iteration` and `prune`. `frontier_size` represents active path length, not a materialized global open list.

## 11. Heuristic registry

Let:

```text
s = min(1, min_(u,v)∈E distance_m(u,v) / haversine_m(u,v))
δ(u,v) = s × haversine_m(u,v) / 1000     # km
v_max = maximum free-flow speed in graph  # km/h
```

Snapshot HCMC hiện tại có `s≈0.824833527` và `v_max=70` km/h. Hai giá trị này được tính lại khi nạp dataset khác; không được hard-code vào thuật toán.

| ID | Formula | Admissible | Consistent | Intended use |
|---|---|---:|---:|---|
| `zero` | `0` | yes | yes | correctness/control baseline |
| `haversine` | `ŵd·δ(n,g)` | yes | yes | distance-aware lower bound |
| `travel_time` | `ŵd·δ + ŵt·(δ/v_max·60)` | yes | yes | default safe informed search |
| `traffic_aware` | distance + predicted time/delay using mean outgoing multiplier | no | no | experimental practical estimate |

The registry clamps every returned value to at least zero.

### 11.1 Why `zero` is safe

`0` never overestimates a non-negative remaining cost. For every edge, `0 <= C(e)+0`, so it is also consistent.

### 11.2 Proof sketch for calibrated Haversine

By construction for every edge `(u,v)`:

```text
δ(u,v) <= distance_km(u,v)
```

Scaled Haversine remains a metric, so:

```text
δ(u,g) <= δ(u,v) + δ(v,g)
```

Because all omitted cost components are non-negative:

```text
h(u)=ŵd·δ(u,g)
    <= ŵd·distance_km(u,v) + h(v)
    <= C(u,v) + h(v)
```

Thus it is consistent; consistency implies admissibility when `h(goal)=0`.

### 11.3 Proof sketch for optimistic travel time

For edge speed `v_e<=v_max` and traffic multiplier `M_e>=1`:

```text
travel_minutes_e = distance_km_e / v_e × 60 × M_e
                 >= distance_km_e / v_max × 60
                 >= δ(u,v) / v_max × 60
```

Applying the metric triangle inequality to both distance and time lower-bound terms gives:

```text
h_time(u) <= [ŵd·distance_e + ŵt·travel_minutes_e] + h_time(v)
           <= C(e) + h_time(v)
```

Delay/risk are omitted but non-negative. Therefore `travel_time` is consistent and admissible.

### 11.4 Why traffic-aware is not guaranteed

It estimates a multiplier from mean traversable outgoing edges at the **current** node and projects it all the way to the goal. That local mean may exceed the cost of a low-congestion route ahead, so the estimate can exceed true remaining cost. Neighboring nodes can also have sharply different means, violating:

```text
h(u) <= C(u,v) + h(v)
```

The API metadata/warning explicitly removes A*/IDA* optimality for this heuristic.

## 12. Tie-breaking and reproducibility

- `RoadGraph` freezes adjacency in dataset insertion order.
- Heap algorithms include a monotonically increasing counter after the numeric priority, avoiding comparisons between node IDs and producing stable equal-priority order.
- Relaxations require a strict improvement with a small `1e-12` tolerance.
- Nearest Neighbor breaks equal matrix costs by stop ID.
- Simulated Annealing uses `random.Random(seed)`, default seed 42.
- Traffic uses SHA-256, not Python's process-randomized `hash()`.

Therefore route/trace is reproducible for the same code, dataset and request. `runtime_ms` and `request_id` are intentionally not deterministic.

## 13. Trace event contract

Every stored event has all fields below; non-applicable numeric values are `null`:

```text
step, event, node_id, parent_id, edge_id, direction,
frontier_size, explored_count, g_cost, h_cost, f_cost,
depth, message
```

| Event | Semantics |
|---|---|
| `start` | initialize a run/wave |
| `iteration` | begin an IDA* f-threshold pass |
| `expand` | remove/select node for expansion |
| `discover` | first discovery in BFS/DFS/Greedy/IDA* |
| `relax` | improve a cost label in heap algorithms |
| `prune` | IDA* `f` exceeds current threshold |
| `finish` | found, unreachable or limit reached |

`frontier_size` is an algorithm-specific count, not a serialized list. The React adapter replays events to derive a visual set of frontier/visited nodes. For Bidirectional Dijkstra the direction field separates waves; for all other algorithms it is `forward`.

Metrics:

- `visited_nodes`: unique node IDs ever expanded;
- `expanded_nodes`: total expansions, including repeated IDA* expansions;
- `generated_nodes`: start plus accepted discoveries/relaxations; not raw edge inspections;
- `frontier_peak`: maximum reported data-structure/active-path size;
- `heuristic_calls`: calls through the registry;
- `path_nodes`, `path_edges`, `hop_count`;
- `runtime_ms`: algorithm timer only;
- `trace_truncated`: event collector hit requested limit.

If trace is disabled, search metrics remain available. If it is truncated, search continues; only visualization detail is lost.

## 14. Multi-stop optimization

### 14.1 Directed metric closure

For `n` stops plus one start, backend runs Dijkstra for every ordered distinct pair, i.e. `(n+1)n` searches. This is a directed matrix: generally `C(a,b) != C(b,a)`. Self-pairs have zero without a search.

All optimizer costs are sums of matrix entries along:

```text
start -> ordered stop 1 -> ... -> ordered stop n [-> start]
```

If no candidate order has finite total cost, API returns `multi_route_unreachable` and reports unreachable directed pairs.

### 14.2 Nearest Neighbor

At each step select the unvisited stop with minimum `(matrix[current,stop], stop_id)`. It is `O(n²)`, deterministic and approximate. It can make an early choice that forces an expensive later leg.

### 14.3 Held–Karp dynamic programming

State `(mask,last)` stores minimum cost from start visiting exactly `mask` and ending at `last`, plus predecessor. It checks the optional return edge when choosing the final state.

- Time `O(n²·2ⁿ)`.
- Memory `O(n·2ⁿ)`.
- Exact for the supplied directed pairwise matrix.
- API cap: 10 stops.

“Exact” chỉ đúng trên ma trận chi phí có hướng được tính với snapshot, scenario và weights hiện tại, dùng Dijkstra chính xác cho từng chặng. Nó không chứng nhận một lịch giao hàng tối ưu ngoài đời thật.

### 14.4 Nearest Neighbor + 2-opt

Starts with greedy order, repeatedly reverses one stop subsequence, and accepts the first strict improvement. Search ends at a local optimum or `max_iterations`. With a directed matrix, reversing a subsequence changes both order and directed leg costs; the implementation re-evaluates the full candidate route, which is correct but not constant-time delta evaluation.

Approximate; no global optimality guarantee.

### 14.5 Seeded Simulated Annealing + 2-opt

Starts from greedy order. Each iteration reverses a random subsequence and accepts:

```text
delta < 0  OR  random() < exp(-delta / temperature)
```

Initial temperature is `max(0.01, 0.25×current_cost)`, then multiplied by `0.995` per iteration. Remaining iteration budget is passed to deterministic 2-opt cleanup. Same seed/input is reproducible; result remains approximate.

## 15. Alternative-route algorithm

For a found primary route with edge list `P`:

1. for each unique `e` in `P`, run Dijkstra while blocking exactly `{e}`;
2. discard unreachable candidates and any identical edge sequence;
3. choose candidate with minimum weighted cost;
4. report blocked edge and `(alternative-primary)/primary × 100`.

This is a bounded “best single-primary-edge exclusion” explanation. It is useful for showing sensitivity and resilience, but it is not Yen's algorithm, not guaranteed to be the global second-simple-shortest path under every definition, and does not impose a disjointness constraint beyond one excluded primary edge per candidate.

## 16. Claim checklist for report/presentation

Safe claims:

- UCS and Dijkstra are equivalent in this implementation.
- Dijkstra/Bidirectional Dijkstra optimize the non-negative weighted cost.
- A* is optimal with `zero`, `haversine` or `travel_time` if expansion limit does not intervene.
- BFS minimizes hops, not composite traffic cost.
- Held–Karp is exact on the computed directed pairwise matrix up to 10 stops.
- 2-opt/SA/Nearest Neighbor are approximate even when they match Held–Karp in one test.

Claims to avoid:

- “A* is always fastest.”
- “Greedy is optimal because it matched one benchmark.”
- “IDA* failed, therefore the destination is unreachable” when status is `limit_reached`.
- “Traffic-aware heuristic is admissible.”
- “Bidirectional always explores half the graph.”
- “Held–Karp finds the globally best real-world delivery plan.”
- “Alternative is the second-shortest route” without the single-edge-exclusion qualifier.

Thay bằng: “Held–Karp tìm thứ tự có tổng chi phí nhỏ nhất trên ma trận pairwise có hướng đã tính, trong giới hạn số stop hỗ trợ và khi mọi pair search hoàn tất.”

## 17. Domain and safety boundary

Các thuật toán chỉ giải bài toán graph của phòng lab giao hàng tại khu vực trung tâm Thành phố Hồ Chí Minh. Snapshot hiện có 1.103 node và 2.279 cung có hướng; topology/tags đến từ một snapshot OSM, còn ETA, congestion, road disruption, flood susceptibility và risk là lớp ước lượng/mô phỏng deterministic.

`traversable=true` chỉ có nghĩa cung được phép tham gia mô hình tìm kiếm. Nó **không** xác nhận đường đó hợp pháp hoặc phù hợp cho xe máy, ô tô, xe tải hay người đi bộ; dataset cũng không mô hình hóa đầy đủ turn restriction, biển cấm, làn xe, giờ cấm hoặc điều kiện hiện trường. Vì vậy output là bằng chứng thuật toán học thuật, không phải hướng dẫn navigation live hay tư vấn pháp lý giao thông.
