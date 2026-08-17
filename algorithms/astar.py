"""A* Search: the minimum-total-cost path guided by an admissible heuristic.

A* expands nodes by `f(n) = g(n) + h(n)`, where `g` is the accumulated weighted cost
(`edge_cost`) and `h` is the straight-line lower bound (`straight_line_heuristic`).
Because `h` is admissible and consistent, the first goal expansion yields the same
minimum-cost path as UCS while typically exploring fewer nodes.

Owned module of the UCS/A* teammate. `AStarAlgorithm` is registered in the core
framework registry so `run_algorithm("astar", ...)` works; `astar()` is the direct
convenience entry point kept for the existing public API.
"""

from __future__ import annotations

import heapq
import time

from algorithms.base import build_result, reconstruct_path
from algorithms.heuristic import edge_cost, straight_line_heuristic
from algorithms.metrics import path_metrics, path_total_cost
from core.search_algorithm import SearchAlgorithm, register_algorithm
from core.search_result import SearchResult, SearchStep
from shared.types import EdgeLike, GraphLike

# Animation reasons are stable UI text (ALGORITHM_SPEC.md § 4.2). The expand reason
# also reports the current f/g/h values so the UI can animate the heuristic's effect.
_REASON_EXPAND = "A* lấy node có f = g + h nhỏ nhất trong hàng đợi ưu tiên (heap)."
_REASON_GOAL = "Đạt node đích: dừng tìm kiếm và dựng lại đường đi (h ước lượng tới đích)."


@register_algorithm
class AStarAlgorithm(SearchAlgorithm):
    """A* Search (priority-queue frontier by f = g + h)."""

    name = "astar"

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

        adjacency: dict[str, list[str]] = {}
        edge_lookup: dict[tuple[str, str], EdgeLike] = {}
        node_lookup: dict[str, object] = {}
        for node in graph.nodes:
            node_lookup[node.id] = node
        for edge in graph.edges:
            adjacency.setdefault(edge.start, []).append(edge.end)
            edge_lookup[(edge.start, edge.end)] = edge

        goal_node = node_lookup[goal]

        def heuristic(node_id: str) -> float:
            return straight_line_heuristic(node_lookup[node_id], goal_node)  # type: ignore[arg-type]

        # Priority queue keyed on f; ties broken deterministically by (f, node-id).
        # Each entry carries the g value so a stale, higher-g entry can be skipped.
        frontier_heap: list[tuple[float, str, float]] = [
            (heuristic(start), start, 0.0)
        ]
        cost_so_far: dict[str, float] = {start: 0.0}
        parent: dict[str, str | None] = {start: None}

        visited_order: list[str] = []
        steps: list[SearchStep] = []
        found = False

        def record_step(current: str, current_g: float, current_h: float, reason: str) -> None:
            if enable_logging:
                steps.append(
                    SearchStep(
                        current_node=current,
                        frontier=sorted(
                            {node for _, node, _ in frontier_heap},
                            key=lambda node: (
                                cost_so_far.get(node, float("inf")) + heuristic(node),
                                node,
                            ),
                        ),
                        reason=(
                            f"{reason} (g = {current_g:.3f}, h = {current_h:.3f}, "
                            f"f = {current_g + current_h:.3f})"
                        ),
                    )
                )

        while frontier_heap:
            _, current, current_g = heapq.heappop(frontier_heap)
            if current_g > cost_so_far.get(current, float("inf")) + 1e-9:
                continue  # stale heap entry from a previously relaxed, better cost

            current_h = heuristic(current)

            if current == goal:
                visited_order.append(current)
                record_step(current, current_g, current_h, _REASON_GOAL)
                found = True
                break

            for neighbor in adjacency.get(current, ()):
                edge = edge_lookup[(current, neighbor)]
                candidate_cost = current_g + edge_cost(edge)
                if candidate_cost < cost_so_far.get(neighbor, float("inf")):
                    cost_so_far[neighbor] = candidate_cost
                    parent[neighbor] = current
                    heapq.heappush(
                        frontier_heap,
                        (candidate_cost + heuristic(neighbor), neighbor, candidate_cost),
                    )

            visited_order.append(current)
            record_step(current, current_g, current_h, _REASON_EXPAND)

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
                "A* chọn đường đi "
                + " → ".join(path)
                + " vì nó có tổng chi phí có trọng số nhỏ nhất (khoảng cách, thời gian, "
                "ùn tắc và rủi ro theo trọng số hiện tại). Heuristic khoảng cách đường "
                "chim bay luôn thấp hơn chi phí thực tế nên A* bảo đảm tối ưu như UCS, "
                "đồng thời thường mở rộng ít node hơn nhờ hướng tìm về phía đích."
            ),
        )


def astar(
    graph: GraphLike,
    start: str,
    goal: str,
    enable_logging: bool = True,
) -> SearchResult:
    """Run A* Search and return the uniform `SearchResult`."""
    return AStarAlgorithm().search(graph, start, goal, enable_logging=enable_logging)
