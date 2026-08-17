"""Uniform-Cost Search (UCS): the minimum-total-cost path.

UCS expands nodes in order of accumulated path cost `g(n)` (computed with the shared
`edge_cost`), so it returns the path with the lowest weighted cost — unlike BFS, which
only optimises the hop count. It is optimal for non-negative edge costs, which holds
for this dataset.

Owned module of the UCS/A* teammate. `UCSAlgorithm` is registered in the core
framework registry so `run_algorithm("ucs", ...)` works; `ucs()` is the direct
convenience entry point kept for the existing public API.
"""

from __future__ import annotations

import heapq
import time

from algorithms.base import build_result, reconstruct_path
from algorithms.heuristic import edge_cost
from algorithms.metrics import path_metrics, path_total_cost
from core.search_algorithm import SearchAlgorithm, register_algorithm
from core.search_result import SearchResult, SearchStep
from shared.types import EdgeLike, GraphLike

# Animation reasons are stable UI text (ALGORITHM_SPEC.md § 4.2); hoisted here so the
# per-frame `SearchStep` construction is a single, readable call site.
_REASON_EXPAND = "UCS lấy node có tổng chi phí nhỏ nhất trong hàng đợi ưu tiên (heap)."
_REASON_GOAL = "Đạt node đích với chi phí tích lũy thấp nhất: dừng tìm kiếm và dựng lại đường đi."


@register_algorithm
class UCSAlgorithm(SearchAlgorithm):
    """Uniform-Cost Search (priority-queue frontier by accumulated cost)."""

    name = "ucs"

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
        # available to reuse. Derive it once (single O(|E|) pass); the id-pair -> edge
        # lookup is reused by the path metrics (same pattern as BFS).
        adjacency: dict[str, list[str]] = {}
        edge_lookup: dict[tuple[str, str], EdgeLike] = {}
        for edge in graph.edges:
            adjacency.setdefault(edge.start, []).append(edge.end)
            edge_lookup[(edge.start, edge.end)] = edge

        # Priority queue keyed on accumulated cost; ties are broken deterministically
        # by the heap entry's (cost, node-id) tuple so results are reproducible.
        frontier_heap: list[tuple[float, str]] = [(0.0, start)]
        cost_so_far: dict[str, float] = {start: 0.0}
        parent: dict[str, str | None] = {start: None}

        visited_order: list[str] = []
        steps: list[SearchStep] = []
        found = False

        def record_step(current: str, reason: str) -> None:
            if enable_logging:
                steps.append(
                    SearchStep(
                        current_node=current,
                        frontier=sorted(
                            {node for _, node in frontier_heap},
                            key=lambda node: (cost_so_far.get(node, float("inf")), node),
                        ),
                        reason=reason,
                    )
                )

        while frontier_heap:
            current_cost, current = heapq.heappop(frontier_heap)
            if current_cost > cost_so_far.get(current, float("inf")):
                continue  # stale heap entry from a previously relaxed, better cost

            if current == goal:
                visited_order.append(current)
                record_step(current, _REASON_GOAL)
                found = True
                break

            for neighbor in adjacency.get(current, ()):
                edge = edge_lookup[(current, neighbor)]
                candidate_cost = current_cost + edge_cost(edge)
                if candidate_cost < cost_so_far.get(neighbor, float("inf")):
                    cost_so_far[neighbor] = candidate_cost
                    parent[neighbor] = current
                    heapq.heappush(frontier_heap, (candidate_cost, neighbor))

            visited_order.append(current)
            record_step(current, _REASON_EXPAND)

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

        # Reconstruct the minimum-cost path from the predecessor map.
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
                "UCS chọn đường đi "
                + " → ".join(path)
                + " vì nó có tổng chi phí có trọng số nhỏ nhất (khoảng cách, thời gian, "
                "ùn tắc và rủi ro theo trọng số hiện tại). Khác với BFS, UCS luôn xét "
                "chi phí cạnh nên đường tối ưu chi phí không nhất thiết ít chặng nhất."
            ),
        )


def ucs(
    graph: GraphLike,
    start: str,
    goal: str,
    enable_logging: bool = True,
) -> SearchResult:
    """Run Uniform-Cost Search and return the uniform `SearchResult`."""
    return UCSAlgorithm().search(graph, start, goal, enable_logging=enable_logging)
