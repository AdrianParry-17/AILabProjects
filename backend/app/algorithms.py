"""Classical graph-search algorithms with a normalized trace contract."""

from __future__ import annotations

import heapq
import itertools
from collections import deque
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from math import inf, isfinite
from time import perf_counter
from typing import Any

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
        self.heuristic_metadata = heuristics.get_metadata(heuristic)
        self._heuristic_cache: dict[str, float] = {}

    def h(self, node_id: str) -> float:
        cached = self._heuristic_cache.get(node_id)
        if cached is not None:
            return cached
        self.heuristic_calls += 1
        value = self.heuristics.estimate(
            self.heuristic, node_id, self.goal, self.graph, self.cost
        )
        self._heuristic_cache[node_id] = value
        return value

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
    counter = itertools.count()
    heap: list[tuple[float, int, str]] = [(0.0, next(counter), context.start)]
    distances = {context.start: 0.0}
    parents: dict[str, tuple[str, str]] = {}
    settled: set[str] = set()
    context.trace.emit("start", node_id=context.start, frontier_size=1, g_cost=0, f_cost=0)
    while heap:
        current_cost, _, node = heapq.heappop(heap)
        if node in settled or current_cost > distances.get(node, inf):
            continue
        if not context.expand(node):
            break
        settled.add(node)
        context.trace.emit(
            "expand", node_id=node, frontier_size=len(heap),
            explored_count=context.expanded_count, g_cost=current_cost, f_cost=current_cost,
        )
        if node == context.goal:
            path, edges = _reconstruct(parents, context.start, context.goal)
            return context.finish(path, edges)
        for edge in context.traversable(context.graph.neighbors(node)):
            child = edge.target
            candidate = current_cost + context.cost.edge_cost(edge)
            if candidate + 1e-12 >= distances.get(child, inf):
                continue
            distances[child] = candidate
            parents[child] = (node, edge.id)
            heapq.heappush(heap, (candidate, next(counter), child))
            context.generated_count += 1
            context.trace.emit(
                "relax", node_id=child, parent_id=node, edge_id=edge.id,
                frontier_size=len(heap), explored_count=context.expanded_count,
                g_cost=candidate, f_cost=candidate,
            )
        context.update_frontier_peak(len(heap))
    return context.finish()


def _astar(context: SearchContext) -> SearchResult:
    trivial = _start_is_goal(context)
    if trivial:
        return trivial
    counter = itertools.count()
    initial_h = context.h(context.start)
    heap: list[tuple[float, int, float, str]] = [
        (initial_h, next(counter), 0.0, context.start)
    ]
    distances = {context.start: 0.0}
    parents: dict[str, tuple[str, str]] = {}
    closed_best: dict[str, float] = {}
    context.trace.emit(
        "start", node_id=context.start, frontier_size=1,
        g_cost=0, h_cost=initial_h, f_cost=initial_h,
    )
    while heap:
        f_cost, _, current_cost, node = heapq.heappop(heap)
        if current_cost > distances.get(node, inf) + 1e-12:
            continue
        if current_cost >= closed_best.get(node, inf) - 1e-12:
            continue
        if not context.expand(node):
            break
        closed_best[node] = current_cost
        node_h = max(0.0, f_cost - current_cost)
        context.trace.emit(
            "expand", node_id=node, frontier_size=len(heap),
            explored_count=context.expanded_count, g_cost=current_cost,
            h_cost=node_h, f_cost=f_cost,
        )
        if node == context.goal:
            path, edges = _reconstruct(parents, context.start, context.goal)
            return context.finish(path, edges)
        for edge in context.traversable(context.graph.neighbors(node)):
            child = edge.target
            candidate = current_cost + context.cost.edge_cost(edge)
            if candidate + 1e-12 >= distances.get(child, inf):
                continue
            distances[child] = candidate
            parents[child] = (node, edge.id)
            child_h = context.h(child)
            child_f = candidate + child_h
            heapq.heappush(heap, (child_f, next(counter), candidate, child))
            context.generated_count += 1
            context.trace.emit(
                "relax", node_id=child, parent_id=node, edge_id=edge.id,
                frontier_size=len(heap), explored_count=context.expanded_count,
                g_cost=candidate, h_cost=child_h, f_cost=child_f,
            )
        context.update_frontier_peak(len(heap))
    return context.finish()


def _greedy(context: SearchContext) -> SearchResult:
    raise NotImplementedError(
        "Greedy Best-First is a placeholder on this branch; the owning teammate "
        "will port the implementation from the reference project in a later commit."
    )


def _bidirectional_dijkstra(context: SearchContext) -> SearchResult:
    raise NotImplementedError(
        "Bidirectional Dijkstra is a placeholder on this branch; the owner "
        "(Huỳnh Minh Hùng) will port the implementation from the reference "
        "project in a later commit."
    )


def _ida_star(context: SearchContext) -> SearchResult:
    raise NotImplementedError(
        "IDA* is a placeholder on this branch; the owner (Huỳnh Minh Hùng) will "
        "port the implementation from the reference project in a later commit."
    )


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
        "dijkstra": _uniform_cost,
        "astar": _astar,
        "greedy_best_first": _greedy,
        "bidirectional_dijkstra": _bidirectional_dijkstra,
        "ida_star": _ida_star,
    }[algorithm]
    return implementation(context)
