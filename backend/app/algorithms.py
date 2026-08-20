"""Classical graph-search algorithms with a normalized trace contract."""

from __future__ import annotations

import heapq
import itertools
from collections import deque
from dataclasses import asdict, dataclass
from math import inf, isfinite
from time import perf_counter
from typing import Any, Iterable

from .costs import CostCalculator
from .domain import DirectedEdge, RoadGraph
from .heuristics import HeuristicRegistry


@dataclass(frozen=True, slots=True)
class AlgorithmMetadata:
    id: str
    label: str
    family: str
    weighted: bool
    heuristic_required: bool
    complete: bool
    optimality: str
    description: str


ALGORITHM_METADATA: dict[str, AlgorithmMetadata] = {
    "bfs": AlgorithmMetadata(
        "bfs", "Breadth-First Search", "uninformed", False, False, True,
        "Minimum hops on a finite graph; not minimum weighted route cost.",
        "Expands the shallowest frontier first.",
    ),
    "dfs": AlgorithmMetadata(
        "dfs", "Depth-First Search", "uninformed", False, False, True,
        "Not optimal.", "Explores one branch deeply before backtracking.",
    ),
    "ucs": AlgorithmMetadata(
        "ucs", "Uniform-Cost Search", "cost-aware", True, False, True,
        "Optimal for non-negative edge costs.",
        "Expands the frontier node with the lowest accumulated weighted cost.",
    ),
    "dijkstra": AlgorithmMetadata(
        "dijkstra", "Dijkstra", "cost-aware", True, False, True,
        "Optimal for non-negative edge costs.",
        "Label-setting shortest path; equivalent to UCS for this graph model.",
    ),
    "astar": AlgorithmMetadata(
        "astar", "A* Search", "informed", True, True, True,
        "Optimal with an admissible, consistent heuristic.",
        "Orders the frontier by accumulated cost plus an estimated remaining cost.",
    ),
    "greedy_best_first": AlgorithmMetadata(
        "greedy_best_first", "Greedy Best-First", "informed", False, True, True,
        "Not optimal.", "Orders the frontier only by estimated remaining cost.",
    ),
    "bidirectional_dijkstra": AlgorithmMetadata(
        "bidirectional_dijkstra", "Bidirectional Dijkstra", "bidirectional", True, False, True,
        "Optimal for non-negative edge costs.",
        "Runs Dijkstra from both endpoints using outgoing and incoming edges.",
    ),
    "ida_star": AlgorithmMetadata(
        "ida_star", "IDA*", "informed", True, True, True,
        "Optimal with an admissible heuristic and finite positive edge costs.",
        "Depth-first iterations use successively larger f-cost thresholds.",
    ),
}


@dataclass(frozen=True, slots=True)
class SearchOptions:
    include_trace: bool = True
    max_trace_events: int = 1_000
    max_expansions: int = 100_000
    blocked_edge_ids: frozenset[str] = frozenset()


@dataclass(slots=True)
class SearchResult:
    algorithm: str
    heuristic: str
    start_id: str
    goal_id: str
    status: str
    found: bool
    path: list[str]
    edge_ids: list[str]
    total_cost: float | None
    metrics: dict[str, Any]
    trace_events: list[dict[str, Any]]
    trace_truncated: bool


class TraceCollector:
    def __init__(self, enabled: bool, limit: int) -> None:
        self.enabled = enabled
        self.limit = max(0, limit)
        self.events: list[dict[str, Any]] = []
        self.truncated = False
        self._seen = 0

    def emit(
        self,
        event: str,
        *,
        node_id: str | None = None,
        parent_id: str | None = None,
        edge_id: str | None = None,
        direction: str = "forward",
        frontier_size: int = 0,
        explored_count: int = 0,
        g_cost: float | None = None,
        h_cost: float | None = None,
        f_cost: float | None = None,
        depth: int | None = None,
        message: str = "",
    ) -> None:
        if not self.enabled:
            return
        step = self._seen
        self._seen += 1
        if len(self.events) >= self.limit:
            self.truncated = True
            return
        self.events.append(
            {
                "step": step,
                "event": event,
                "node_id": node_id,
                "parent_id": parent_id,
                "edge_id": edge_id,
                "direction": direction,
                "frontier_size": frontier_size,
                "explored_count": explored_count,
                "g_cost": _round_optional(g_cost),
                "h_cost": _round_optional(h_cost),
                "f_cost": _round_optional(f_cost),
                "depth": depth,
                "message": message,
            }
        )


def _round_optional(value: float | None) -> float | None:
    return None if value is None or not isfinite(value) else round(value, 9)


class SearchContext:
    def __init__(
        self,
        algorithm: str,
        graph: RoadGraph,
        cost: CostCalculator,
        heuristics: HeuristicRegistry,
        heuristic: str,
        start: str,
        goal: str,
        options: SearchOptions,
    ) -> None:
        self.algorithm = algorithm
        self.graph = graph
        self.cost = cost
        self.heuristics = heuristics
        self.heuristic = heuristic
        self.start = start
        self.goal = goal
        self.options = options
        self.trace = TraceCollector(options.include_trace, options.max_trace_events)
        self.started_at = perf_counter()
        self.expanded_count = 0
        self.expanded_unique: set[str] = set()
        self.generated_count = 1
        self.frontier_peak = 1
        self.heuristic_calls = 0
        self.limit_reached = False

    def h(self, node_id: str) -> float:
        self.heuristic_calls += 1
        return self.heuristics.estimate(
            self.heuristic, node_id, self.goal, self.graph, self.cost
        )

    def traversable(self, edges: Iterable[DirectedEdge]) -> Iterable[DirectedEdge]:
        for edge in edges:
            if edge.id not in self.options.blocked_edge_ids and self.cost.is_traversable(edge):
                yield edge

    def expand(self, node_id: str) -> bool:
        if self.expanded_count >= self.options.max_expansions:
            self.limit_reached = True
            return False
        self.expanded_count += 1
        self.expanded_unique.add(node_id)
        return True

    def update_frontier_peak(self, size: int) -> None:
        self.frontier_peak = max(self.frontier_peak, size)

    def finish(
        self,
        path: list[str] | None = None,
        edge_ids: list[str] | None = None,
    ) -> SearchResult:
        path = path or []
        edge_ids = edge_ids or []
        found = bool(path)
        status = "found" if found else ("limit_reached" if self.limit_reached else "unreachable")
        total_cost = (
            sum(self.cost.edge_cost(self.graph.edge(edge_id)) for edge_id in edge_ids)
            if found
            else None
        )
        elapsed_ms = (perf_counter() - self.started_at) * 1000
        self.trace.emit(
            "finish",
            node_id=path[-1] if path else None,
            frontier_size=0,
            explored_count=self.expanded_count,
            g_cost=total_cost,
            message=status,
        )
        metrics = {
            "runtime_ms": round(elapsed_ms, 6),
            "visited_nodes": len(self.expanded_unique),
            "expanded_nodes": self.expanded_count,
            "generated_nodes": self.generated_count,
            "frontier_peak": self.frontier_peak,
            "heuristic_calls": self.heuristic_calls,
            "path_nodes": len(path),
            "path_edges": len(edge_ids),
            "hop_count": len(edge_ids),
            "path_cost": round(total_cost, 9) if total_cost is not None else None,
            "trace_truncated": self.trace.truncated,
        }
        return SearchResult(
            algorithm=self.algorithm,
            heuristic=self.heuristic,
            start_id=self.start,
            goal_id=self.goal,
            status=status,
            found=found,
            path=path,
            edge_ids=edge_ids,
            total_cost=total_cost,
            metrics=metrics,
            trace_events=self.trace.events,
            trace_truncated=self.trace.truncated,
        )


def algorithm_metadata() -> list[dict[str, Any]]:
    return [asdict(item) for item in ALGORITHM_METADATA.values()]


def _reconstruct(
    parents: dict[str, tuple[str, str]], start: str, goal: str
) -> tuple[list[str], list[str]]:
    if start == goal:
        return [start], []
    if goal not in parents:
        return [], []
    nodes = [goal]
    edges: list[str] = []
    current = goal
    while current != start:
        parent, edge_id = parents[current]
        nodes.append(parent)
        edges.append(edge_id)
        current = parent
    nodes.reverse()
    edges.reverse()
    return nodes, edges


def _start_is_goal(context: SearchContext) -> SearchResult | None:
    if context.start != context.goal:
        return None
    context.trace.emit(
        "start", node_id=context.start, g_cost=0, h_cost=0, f_cost=0,
        message="Start node is the goal",
    )
    return context.finish([context.start], [])


def _bfs(context: SearchContext) -> SearchResult:
    trivial = _start_is_goal(context)
    if trivial:
        return trivial
    queue: deque[tuple[str, int]] = deque([(context.start, 0)])
    discovered = {context.start}
    parents: dict[str, tuple[str, str]] = {}
    g_cost = {context.start: 0.0}
    context.trace.emit("start", node_id=context.start, frontier_size=1, g_cost=0, depth=0)
    while queue:
        node, depth = queue.popleft()
        if not context.expand(node):
            break
        context.trace.emit(
            "expand", node_id=node, frontier_size=len(queue),
            explored_count=context.expanded_count, g_cost=g_cost[node], depth=depth,
        )
        if node == context.goal:
            path, edges = _reconstruct(parents, context.start, context.goal)
            return context.finish(path, edges)
        for edge in context.traversable(context.graph.neighbors(node)):
            child = edge.target
            if child in discovered:
                continue
            discovered.add(child)
            parents[child] = (node, edge.id)
            g_cost[child] = g_cost[node] + context.cost.edge_cost(edge)
            queue.append((child, depth + 1))
            context.generated_count += 1
            context.trace.emit(
                "discover", node_id=child, parent_id=node, edge_id=edge.id,
                frontier_size=len(queue), explored_count=context.expanded_count,
                g_cost=g_cost[child], depth=depth + 1,
            )
        context.update_frontier_peak(len(queue))
    return context.finish()


def _dfs(context: SearchContext) -> SearchResult:
    trivial = _start_is_goal(context)
    if trivial:
        return trivial
    stack: list[tuple[str, int]] = [(context.start, 0)]
    discovered = {context.start}
    parents: dict[str, tuple[str, str]] = {}
    g_cost = {context.start: 0.0}
    context.trace.emit("start", node_id=context.start, frontier_size=1, g_cost=0, depth=0)
    while stack:
        node, depth = stack.pop()
        if not context.expand(node):
            break
        context.trace.emit(
            "expand", node_id=node, frontier_size=len(stack),
            explored_count=context.expanded_count, g_cost=g_cost[node], depth=depth,
        )
        if node == context.goal:
            path, edges = _reconstruct(parents, context.start, context.goal)
            return context.finish(path, edges)
        candidates = list(context.traversable(context.graph.neighbors(node)))
        for edge in reversed(candidates):
            child = edge.target
            if child in discovered:
                continue
            discovered.add(child)
            parents[child] = (node, edge.id)
            g_cost[child] = g_cost[node] + context.cost.edge_cost(edge)
            stack.append((child, depth + 1))
            context.generated_count += 1
            context.trace.emit(
                "discover", node_id=child, parent_id=node, edge_id=edge.id,
                frontier_size=len(stack), explored_count=context.expanded_count,
                g_cost=g_cost[child], depth=depth + 1,
            )
        context.update_frontier_peak(len(stack))
    return context.finish()

def _uniform_cost(context: SearchContext) -> SearchResult:
    trivial = _start_is_goal(context)
    if trivial:
        return trivial

    # Every frontier item is (total_cost, tie_breaker, node_id).
    # total_cost decides the priority.  tie_breaker is just a counter so two
    # items with the same cost are never compared by their node ids.
    tie_breaker = itertools.count()
    frontier: list[tuple[float, int, str]] = [
        (0.0, next(tie_breaker), context.start)
    ]

    # best_cost[node] = cheapest known cost to reach "node" so far.
    best_cost = {context.start: 0.0}

    # parents[node] = (previous node, edge used) to rebuild the path later.
    parents: dict[str, tuple[str, str]] = {}

    context.trace.emit(
        "start", node_id=context.start, frontier_size=1, g_cost=0, f_cost=0,
    )

    while frontier:
        total_cost, _, current_node = heapq.heappop(frontier)

        # The same node can be pushed into the frontier several times, each
        # time with a better cost.  Skip the old, more expensive copies.
        if total_cost > best_cost.get(current_node, inf):
            continue

        if not context.expand(current_node):
            break

        context.trace.emit(
            "expand", node_id=current_node, frontier_size=len(frontier),
            explored_count=context.expanded_count,
            g_cost=total_cost, f_cost=total_cost,
        )

        # The first time a node is popped its cost is final, so if it is the
        # goal node we can stop and rebuild the path.
        if current_node == context.goal:
            path, edges = _reconstruct(parents, context.start, context.goal)
            return context.finish(path, edges)

        for edge in context.traversable(context.graph.neighbors(current_node)):
            neighbor = edge.target
            new_cost = total_cost + context.cost.edge_cost(edge)

            # Keep the neighbor only if this route improves its best cost.
            if new_cost >= best_cost.get(neighbor, inf):
                continue

            best_cost[neighbor] = new_cost
            parents[neighbor] = (current_node, edge.id)
            heapq.heappush(frontier, (new_cost, next(tie_breaker), neighbor))

            context.generated_count += 1
            context.trace.emit(
                "relax", node_id=neighbor, parent_id=current_node, edge_id=edge.id,
                frontier_size=len(frontier), explored_count=context.expanded_count,
                g_cost=new_cost, f_cost=new_cost,
            )

        context.update_frontier_peak(len(frontier))

    return context.finish()


def _dijkstra(context: SearchContext) -> SearchResult:
    trivial = _start_is_goal(context)
    if trivial:
        return trivial

    counter = itertools.count()
    heap: list[tuple[float, int, str]] = [(0.0, next(counter), context.start)]

    distances = {context.start: 0.0}
    parents: dict[str, tuple[str, str]] = {}
    settled: set[str] = set()

    context.trace.emit("start", node_id=context.start, frontier_size=1, g_cost=0, f_cost=0)

    while heap:
        distance, _, node = heapq.heappop(heap)

        if (node in settled) or distance > distances.get(node, inf):
            continue
        if not context.expand(node):
            break

        settled.add(node)
        context.trace.emit("expand", node_id=node, frontier_size=len(heap),
                           explored_count=context.expanded_count,g_cost=distance,f_cost=distance)

        if node == context.goal:
            path, edges = _reconstruct(parents, context.start, context.goal)
            return context.finish(path, edges)

        for edge in context.traversable(context.graph.neighbors(node)):
            neighbor = edge.target
            new_distance = distance + context.cost.edge_cost(edge)

            if new_distance + 1e-12 >= distances.get(neighbor, inf):
                continue

            distances[neighbor] = new_distance
            parents[neighbor] = (node, edge.id)

            heapq.heappush(heap, (new_distance, next(counter), neighbor))

            context.generated_count += 1
            context.trace.emit("relax", node_id=neighbor, parent_id=node,edge_id=edge.id,frontier_size=len(heap),
                               explored_count=context.expanded_count, g_cost=new_distance, f_cost=new_distance)

        context.update_frontier_peak(len(heap))
    return context.finish()


def _astar(context: SearchContext) -> SearchResult:
    trivial = _start_is_goal(context)
    if trivial:
        return trivial

    # Every frontier item is (f_cost, tie_breaker, g_cost, node_id).
    # tie_breaker avoids comparing two node ids with the same f_cost.
    tie_breaker = itertools.count()
    initial_h = context.h(context.start)
    frontier: list[tuple[float, int, float, str]] = [
        (initial_h, next(tie_breaker), 0.0, context.start)
    ]

    # best_g[node] = cheapest known cost to reach "node" so far.
    best_g = {context.start: 0.0}

    # closed[node] = the cost at which "node" was last expanded.  It stops us
    # from expanding a node a second time at the same (or worse) cost.
    closed: dict[str, float] = {}

    # parents[node] = (previous node, edge used) to rebuild the path later.
    parents: dict[str, tuple[str, str]] = {}

    context.trace.emit(
        "start", node_id=context.start, frontier_size=1,
        g_cost=0, h_cost=initial_h, f_cost=initial_h,
    )

    while frontier:
        f_cost, _, g_cost, current_node = heapq.heappop(frontier)

        # 1e-12 is a tiny tolerance so near-equal floating-point numbers are
        # treated as equal instead of causing spurious re-expansions.
        if g_cost > best_g.get(current_node, inf) + 1e-12:
            continue
        if g_cost >= closed.get(current_node, inf) - 1e-12:
            continue

        if not context.expand(current_node):
            break

        closed[current_node] = g_cost
        h_cost = max(0.0, f_cost - g_cost)

        context.trace.emit(
            "expand", node_id=current_node, frontier_size=len(frontier),
            explored_count=context.expanded_count, g_cost=g_cost,
            h_cost=h_cost, f_cost=f_cost,
        )

        if current_node == context.goal:
            path, edges = _reconstruct(parents, context.start, context.goal)
            return context.finish(path, edges)

        for edge in context.traversable(context.graph.neighbors(current_node)):
            neighbor = edge.target
            new_g = g_cost + context.cost.edge_cost(edge)

            if new_g + 1e-12 >= best_g.get(neighbor, inf):
                continue

            best_g[neighbor] = new_g
            parents[neighbor] = (current_node, edge.id)

            new_h = context.h(neighbor)
            new_f = new_g + new_h
            heapq.heappush(frontier, (new_f, next(tie_breaker), new_g, neighbor))

            context.generated_count += 1
            context.trace.emit(
                "relax", node_id=neighbor, parent_id=current_node, edge_id=edge.id,
                frontier_size=len(frontier), explored_count=context.expanded_count,
                g_cost=new_g, h_cost=new_h, f_cost=new_f,
            )

        context.update_frontier_peak(len(frontier))

    return context.finish()


def _greedy(context: SearchContext) -> SearchResult:
    trivial = _start_is_goal(context)
    if trivial:
        return trivial
    counter = itertools.count()
    initial_h = context.h(context.start)
    heap: list[tuple[float, int, str]] = [(initial_h, next(counter), context.start)]
    discovered = {context.start}
    parents: dict[str, tuple[str, str]] = {}
    g_cost = {context.start: 0.0}
    context.trace.emit(
        "start", node_id=context.start, frontier_size=1,
        g_cost=0, h_cost=initial_h, f_cost=initial_h,
    )
    while heap:
        node_h, _, node = heapq.heappop(heap)
        if not context.expand(node):
            break
        context.trace.emit(
            "expand", node_id=node, frontier_size=len(heap),
            explored_count=context.expanded_count, g_cost=g_cost[node],
            h_cost=node_h, f_cost=node_h,
        )
        if node == context.goal:
            path, edges = _reconstruct(parents, context.start, context.goal)
            return context.finish(path, edges)
        for edge in context.traversable(context.graph.neighbors(node)):
            child = edge.target
            if child in discovered:
                continue
            discovered.add(child)
            parents[child] = (node, edge.id)
            g_cost[child] = g_cost[node] + context.cost.edge_cost(edge)
            child_h = context.h(child)
            heapq.heappush(heap, (child_h, next(counter), child))
            context.generated_count += 1
            context.trace.emit(
                "discover", node_id=child, parent_id=node, edge_id=edge.id,
                frontier_size=len(heap), explored_count=context.expanded_count,
                g_cost=g_cost[child], h_cost=child_h, f_cost=child_h,
            )
        context.update_frontier_peak(len(heap))
    return context.finish()


def _bidirectional_dijkstra(context: SearchContext) -> SearchResult:
    trivial = _start_is_goal(context)
    if trivial:
        return trivial
    counter = itertools.count()
    forward_heap: list[tuple[float, int, str]] = [(0.0, next(counter), context.start)]
    backward_heap: list[tuple[float, int, str]] = [(0.0, next(counter), context.goal)]
    forward_dist = {context.start: 0.0}
    backward_dist = {context.goal: 0.0}
    forward_parent: dict[str, tuple[str, str]] = {}
    backward_next: dict[str, tuple[str, str]] = {}
    forward_settled: set[str] = set()
    backward_settled: set[str] = set()
    best = inf
    meeting: str | None = None
    context.generated_count = 2
    context.frontier_peak = 2
    context.trace.emit(
        "start", node_id=context.start, direction="forward", frontier_size=2,
        g_cost=0, message=f"Forward from {context.start}; backward from {context.goal}",
    )

    def clean(heap: list[tuple[float, int, str]], distances: dict[str, float], settled: set[str]) -> None:
        while heap and (heap[0][2] in settled or heap[0][0] > distances.get(heap[0][2], inf)):
            heapq.heappop(heap)

    while forward_heap and backward_heap:
        clean(forward_heap, forward_dist, forward_settled)
        clean(backward_heap, backward_dist, backward_settled)
        if not forward_heap or not backward_heap:
            break
        if forward_heap[0][0] + backward_heap[0][0] >= best - 1e-12:
            break
        go_forward = forward_heap[0][0] <= backward_heap[0][0]
        heap = forward_heap if go_forward else backward_heap
        distance = forward_dist if go_forward else backward_dist
        settled = forward_settled if go_forward else backward_settled
        current_cost, _, node = heapq.heappop(heap)
        if node in settled:
            continue
        if not context.expand(node):
            break
        settled.add(node)
        direction = "forward" if go_forward else "backward"
        context.trace.emit(
            "expand", node_id=node, direction=direction,
            frontier_size=len(forward_heap) + len(backward_heap),
            explored_count=context.expanded_count, g_cost=current_cost,
        )

        other_dist = backward_dist if go_forward else forward_dist
        if node in other_dist and current_cost + other_dist[node] < best:
            best = current_cost + other_dist[node]
            meeting = node

        edges = context.graph.neighbors(node) if go_forward else context.graph.incoming(node)
        for edge in context.traversable(edges):
            child = edge.target if go_forward else edge.source
            candidate = current_cost + context.cost.edge_cost(edge)
            if candidate + 1e-12 >= distance.get(child, inf):
                continue
            distance[child] = candidate
            if go_forward:
                forward_parent[child] = (node, edge.id)
            else:
                backward_next[child] = (node, edge.id)
            heapq.heappush(heap, (candidate, next(counter), child))
            context.generated_count += 1
            context.trace.emit(
                "relax", node_id=child, parent_id=node, edge_id=edge.id,
                direction=direction,
                frontier_size=len(forward_heap) + len(backward_heap),
                explored_count=context.expanded_count, g_cost=candidate,
            )
            if child in other_dist and candidate + other_dist[child] < best:
                best = candidate + other_dist[child]
                meeting = child
        context.update_frontier_peak(len(forward_heap) + len(backward_heap))

    if meeting is None:
        return context.finish()
    prefix_nodes, prefix_edges = _reconstruct(forward_parent, context.start, meeting)
    if not prefix_nodes:
        return context.finish()
    suffix_nodes: list[str] = []
    suffix_edges: list[str] = []
    current = meeting
    while current != context.goal:
        if current not in backward_next:
            return context.finish()
        next_node, edge_id = backward_next[current]
        suffix_nodes.append(next_node)
        suffix_edges.append(edge_id)
        current = next_node
    return context.finish(prefix_nodes + suffix_nodes, prefix_edges + suffix_edges)


def _ida_star(context: SearchContext) -> SearchResult:
    trivial = _start_is_goal(context)
    if trivial:
        return trivial
    threshold = context.h(context.start)
    path_nodes = [context.start]
    path_edges: list[str] = []
    on_path = {context.start}
    found_nodes: list[str] | None = None
    found_edges: list[str] | None = None
    context.trace.emit(
        "start", node_id=context.start, frontier_size=1,
        g_cost=0, h_cost=threshold, f_cost=threshold, depth=0,
    )

    def visit(node: str, g_cost: float, bound: float, depth: int) -> float:
        nonlocal found_nodes, found_edges
        heuristic = context.h(node)
        f_cost = g_cost + heuristic
        if f_cost > bound + 1e-12:
            context.trace.emit(
                "prune", node_id=node, frontier_size=len(path_nodes),
                explored_count=context.expanded_count, g_cost=g_cost,
                h_cost=heuristic, f_cost=f_cost, depth=depth,
                message=f"f-cost exceeds threshold {bound:.6f}",
            )
            return f_cost
        if not context.expand(node):
            return inf
        context.trace.emit(
            "expand", node_id=node, frontier_size=len(path_nodes),
            explored_count=context.expanded_count, g_cost=g_cost,
            h_cost=heuristic, f_cost=f_cost, depth=depth,
        )
        if node == context.goal:
            found_nodes = list(path_nodes)
            found_edges = list(path_edges)
            return -inf

        next_bound = inf
        for edge in context.traversable(context.graph.neighbors(node)):
            child = edge.target
            if child in on_path:
                continue
            context.generated_count += 1
            path_nodes.append(child)
            path_edges.append(edge.id)
            on_path.add(child)
            context.update_frontier_peak(len(path_nodes))
            context.trace.emit(
                "discover", node_id=child, parent_id=node, edge_id=edge.id,
                frontier_size=len(path_nodes), explored_count=context.expanded_count,
                g_cost=g_cost + context.cost.edge_cost(edge), depth=depth + 1,
            )
            value = visit(child, g_cost + context.cost.edge_cost(edge), bound, depth + 1)
            if value == -inf:
                return -inf
            next_bound = min(next_bound, value)
            on_path.remove(child)
            path_edges.pop()
            path_nodes.pop()
            if context.limit_reached:
                return inf
        return next_bound

    while isfinite(threshold) and not context.limit_reached:
        context.trace.emit(
            "iteration", node_id=context.start, frontier_size=1,
            explored_count=context.expanded_count, f_cost=threshold,
            message=f"IDA* threshold {threshold:.6f}",
        )
        next_threshold = visit(context.start, 0.0, threshold, 0)
        if next_threshold == -inf:
            return context.finish(found_nodes, found_edges)
        if not isfinite(next_threshold):
            break
        threshold = next_threshold
    return context.finish()


def run_algorithm(
    graph: RoadGraph,
    cost: CostCalculator,
    heuristics: HeuristicRegistry,
    algorithm: str,
    heuristic: str,
    start: str,
    goal: str,
    options: SearchOptions | None = None,
) -> SearchResult:
    if algorithm not in ALGORITHM_METADATA:
        choices = ", ".join(ALGORITHM_METADATA)
        raise ValueError(f"Unknown algorithm {algorithm!r}; choose one of: {choices}")
    if start not in graph.nodes:
        raise ValueError(f"Unknown start node {start!r}")
    if goal not in graph.nodes:
        raise ValueError(f"Unknown goal node {goal!r}")
    heuristics.get_metadata(heuristic)
    context = SearchContext(
        algorithm, graph, cost, heuristics, heuristic, start, goal, options or SearchOptions()
    )
    implementation = {
        "bfs": _bfs,
        "dfs": _dfs,
        "ucs": _uniform_cost,
        "dijkstra": _dijkstra,
        "astar": _astar,
        "greedy_best_first": _greedy,
        "bidirectional_dijkstra": _bidirectional_dijkstra,
        "ida_star": _ida_star,
    }[algorithm]
    return implementation(context)
