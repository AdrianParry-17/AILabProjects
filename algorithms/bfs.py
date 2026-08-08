"""Breadth-First Search: the fewest-hop path.

BFS finds the path with the fewest edges (fewest hops). It is hop-optimal but NOT
cost/distance/time-optimal, because edge costs differ upstream (docs/BFS_SPEC.md).

Owned module of the BFS teammate. `BFSAlgorithm` is registered in the core framework
registry so `run_algorithm("bfs", ...)` works; `bfs()` is the direct convenience
entry point kept for the existing public API.
"""

from __future__ import annotations

import time
from collections import deque

from algorithms.base import build_result, reconstruct_path
from algorithms.heuristic import edge_cost
from algorithms.metrics import path_metrics, path_total_cost
from core.search_algorithm import SearchAlgorithm, register_algorithm
from core.search_result import SearchResult, SearchStep
from shared.types import EdgeLike, GraphLike

# Animation reasons are stable UI text (docs/BFS_SPEC.md § 10); hoisted here so the
# per-frame `SearchStep` construction is a single, readable call site.
_REASON_EXPAND = "Duyệt theo BFS (FIFO): lấy node sớm nhất trong hàng đợi."
_REASON_GOAL = "Đạt node đích: dừng tìm kiếm và dựng lại đường đi."


@register_algorithm
class BFSAlgorithm(SearchAlgorithm):
    """Breadth-First Search (FIFO frontier) with per-node animation steps."""

    name = "bfs"

    def search(
        self,
        graph: GraphLike,
        start: str,
        goal: str,
        **kwargs: object,
    ) -> SearchResult:
        enable_logging = bool(kwargs.get("enable_logging", True))
        started = time.perf_counter()
        node_ids = {node.id for node in graph.nodes}

        if start not in node_ids or goal not in node_ids:
            missing = [name for name in (start, goal) if name not in node_ids]
            return build_result(
                path=[],
                visited_order=[],
                steps=[],
                total_distance_km=0.0,
                total_time_min=0.0,
                total_cost=0.0,
                started=started,
                explanation="Không tìm thấy node trong đồ thị: "
                + ", ".join(map(str, missing))
                + ".",
            )

        if start == goal:
            return build_result(
                path=[start],
                visited_order=[start],
                steps=[],
                total_distance_km=0.0,
                total_time_min=0.0,
                total_cost=0.0,
                started=started,
                explanation="Điểm bắt đầu trùng điểm đến. Đường đi chỉ gồm node khởi đầu.",
            )

        # `GraphLike` exposes only flat `.nodes`/`.edges`, so no adjacency index is
        # available to reuse. Derive it here once (single O(|E|) pass) instead of
        # scanning every edge for each expanded node, which would be O(|V|·|E|).
        # The same pass also yields the id-pair -> edge lookup reused by the metrics.
        adjacency: dict[str, list[str]] = {}
        edge_lookup: dict[tuple[str, str], EdgeLike] = {}
        for edge in graph.edges:
            adjacency.setdefault(edge.start, []).append(edge.end)
            edge_lookup[(edge.start, edge.end)] = edge

        parent: dict[str, str | None] = {start: None}
        discovered: set[str] = {start}
        queue: deque[str] = deque([start])

        visited_order: list[str] = []
        steps: list[SearchStep] = []
        found = False

        def record_step(current: str, frontier: deque[str], reason: str) -> None:
            if enable_logging:
                steps.append(
                    SearchStep(
                        current_node=current,
                        frontier=list(frontier),
                        reason=reason,
                    )
                )

        while queue:
            current = queue.popleft()
            if current == goal:
                visited_order.append(current)
                record_step(current, queue, _REASON_GOAL)
                found = True
                break

            for neighbor in adjacency.get(current, ()):
                if neighbor in discovered:
                    continue
                discovered.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

            visited_order.append(current)
            record_step(current, queue, _REASON_EXPAND)

        if not found:
            return build_result(
                path=[],
                visited_order=visited_order,
                steps=steps if enable_logging else [],
                total_distance_km=0.0,
                total_time_min=0.0,
                total_cost=0.0,
                started=started,
                explanation="Không tồn tại đường đi giữa hai điểm trong đồ thị.",
            )

        # Reconstruct the fewest-hop path from the parent map.
        path = reconstruct_path(parent, goal)

        distance, time_min = path_metrics(graph, path, edge_lookup)
        total_cost = path_total_cost(graph, path, edge_lookup, cost_fn=edge_cost)

        return build_result(
            path=path,
            visited_order=visited_order,
            steps=steps if enable_logging else [],
            total_distance_km=distance,
            total_time_min=time_min,
            total_cost=total_cost,
            started=started,
            explanation=(
                "BFS chọn đường đi "
                + " → ".join(path)
                + " vì nó có số chặng ít nhất (ít bước nhất), không phụ thuộc vào chi phí hay "
                "độ dài. Do đó đường này có thể không tối ưu về tổng chi phí/thời gian so với "
                "UCS/A* nếu có đoạn kẹt xe."
            ),
        )


def bfs(
    graph: GraphLike,
    start: str,
    goal: str,
    enable_logging: bool = True,
) -> SearchResult:
    """Run Breadth-First Search and return the uniform `SearchResult`."""
    return BFSAlgorithm().search(
        graph, start, goal, enable_logging=enable_logging
    )
