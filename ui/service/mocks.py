"""Deterministic mock search algorithms for the GUI service (GUI_ROADMAP § 6).

Until the DFS/UCS/Greedy/A* teammates land their real modules, the service
serves these mocks so the UI can demo every algorithm. The mocks satisfy the
§ 6.6 invariants and reuse the same shared helpers as the real algorithms
(``algorithms.metrics`` / ``algorithms.heuristic``) so their metric numbers are
computed identically.

Every mock is a pure function (graph, start, goal) -> ``SearchResult``. It
builds out-adjacency in the **same edge order** as ``run_algorithm("bfs", ...)``
(§ 6.1) and breaks ties deterministically (by adjacency order via an insertion
counter), so results are reproducible.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from heapq import heappop, heappush
from typing import Protocol

from algorithms.heuristic import DEFAULT_WEIGHTS, edge_cost
from algorithms.metrics import path_metrics, path_total_cost
from core.search_result import SearchResult, SearchStep
from shared.helpers import haversine_m
from shared.types import EdgeLike, GraphLike

__all__ = [
    "MockAstar",
    "MockDFS",
    "MockGreedy",
    "MockProvider",
    "MockUCS",
]


class MockProvider(Protocol):
    """Structural contract implemented by every mock algorithm.

    Kept as a ``Protocol`` so the catalog can interop with any mock without a
    shared base-class requirement (GUI_ROADMAP § 13: mocks are internal).
    """

    name: str

    def search(
        self,
        graph: GraphLike,
        start: str,
        goal: str,
        *,
        enable_logging: bool = True,
    ) -> SearchResult:
        """Run a deterministic mock search and return a uniform ``SearchResult``."""


class _MockBase(ABC):
    """Shared machinery for the mock algorithms (adjacency, metrics, result)."""

    name = "abstract"

    # -- shared graph setup (deterministic; same edge order as BFS, § 6.1) --

    @staticmethod
    def _setup(graph: GraphLike) -> tuple[dict[str, list[str]], dict[tuple[str, str], EdgeLike]]:
        adjacency: dict[str, list[str]] = {}
        edge_lookup: dict[tuple[str, str], EdgeLike] = {}
        for edge in graph.edges:
            adjacency.setdefault(edge.start, []).append(edge.end)
            edge_lookup[(edge.start, edge.end)] = edge
        return adjacency, edge_lookup

    # -- deterministic timing (never measures real time; § 6.3). Keyed off the
    # -- visited count so metrics are unchanged with enable_logging=False. --

    @staticmethod
    def _mock_time(visited_count: int) -> float:
        return round(0.8 * (visited_count + 1), 3)

    # -- explanation per § 6.4: Vietnamese with the ``(mô phỏng)`` marker --

    def _explanation(self, path: list[str], rule: str) -> str:
        label = self.__class__.__name__.removeprefix("Mock")
        hops = len(path) - 1 if path else 0
        return (
            f"{label} - mô phỏng: chọn đường "
            + (" → ".join(path) if path else "(không có đường)")
            + f" ({hops} bước). "
            + rule
        )

    @staticmethod
    def _trivial_explanation(name: str, *, start_equals_goal: bool) -> str:
        if start_equals_goal:
            return (
                f"{name} - mô phỏng: điểm bắt đầu trùng điểm đến, "
                "đường đi chỉ gồm node khởi đầu."
            )
        return f"{name} - mô phỏng: không tìm thấy node trong đồ thị."

    # -- uniform result assembly (metrics via shared helpers) --

    def _result(
        self,
        *,
        path: list[str],
        visited_order: list[str],
        steps: list[SearchStep],
        explanation: str,
        graph: GraphLike,
        edge_lookup: dict[tuple[str, str], EdgeLike],
        enable_logging: bool,
    ) -> SearchResult:
        distance, time_min = path_metrics(graph, path, edge_lookup)
        total_cost = path_total_cost(graph, path, edge_lookup, cost_fn=edge_cost)
        return SearchResult(
            path=path,
            visited_nodes=visited_order,
            steps=steps if enable_logging else [],
            total_distance_km=round(distance, 3),
            total_time_min=round(time_min, 3),
            total_cost=round(total_cost, 3),
            processing_time_ms=self._mock_time(len(visited_order)),
            explanation=explanation,
        )

    def _early(
        self,
        *,
        graph: GraphLike,
        start: str,
        goal: str,
        start_equals_goal: bool,
    ) -> SearchResult | None:
        """Return the trivial § 6.5 result when the search cannot expand."""
        label = self.__class__.__name__.removeprefix("Mock")
        node_ids = {node.id for node in graph.nodes}
        if start_equals_goal:
            return SearchResult(
                path=[start],
                visited_nodes=[start],
                steps=[],
                total_distance_km=0.0,
                total_time_min=0.0,
                total_cost=0.0,
                processing_time_ms=self._mock_time(1),
                explanation=self._trivial_explanation(label, start_equals_goal=True),
            )
        if start not in node_ids or goal not in node_ids:
            return SearchResult(
                path=[],
                visited_nodes=[],
                steps=[],
                total_distance_km=0.0,
                total_time_min=0.0,
                total_cost=0.0,
                processing_time_ms=self._mock_time(0),
                explanation=self._trivial_explanation(label, start_equals_goal=False),
            )
        return None

    @abstractmethod
    def search(
        self,
        graph: GraphLike,
        start: str,
        goal: str,
        *,
        enable_logging: bool = True,
    ) -> SearchResult:
        ...


class MockDFS(_MockBase):
    """Depth-First Search (LIFO stack frontier) — mock (GUI § 6)."""

    name = "dfs"

    def search(
        self,
        graph: GraphLike,
        start: str,
        goal: str,
        *,
        enable_logging: bool = True,
    ) -> SearchResult:
        early = self._early(
            graph=graph,
            start=start,
            goal=goal,
            start_equals_goal=start == goal,
        )
        if early is not None:
            return early

        adjacency, edge_lookup = self._setup(graph)
        parent: dict[str, str | None] = {start: None}
        visited: set[str] = set()
        stack: list[str] = [start]
        visited_order: list[str] = []
        steps: list[SearchStep] = []
        found = False

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            visited_order.append(current)
            if current == goal:
                # § 6.6: last frontier must be empty at the final step.
                if enable_logging:
                    steps.append(
                        SearchStep(
                            current_node=current,
                            frontier=[],
                            reason="DFS - mô phỏng: đạt node đích, dừng tìm kiếm.",
                        )
                    )
                found = True
                break
            if enable_logging:
                steps.append(
                    SearchStep(
                        current_node=current,
                        frontier=list(stack),
                        reason="DFS - mô phỏng: mở rộng node theo ngăn xếp (LIFO).",
                    )
                )
            # Push neighbors reversed so the first neighbor (in adjacency order)
            # sits on top of the stack (§ 6.1 deterministic tie-break).
            for neighbor in reversed(adjacency.get(current, ())):
                if neighbor not in visited and neighbor not in parent:
                    parent[neighbor] = current
                    stack.append(neighbor)

        if not found:
            rule = "Không tồn tại đường đi giữa hai điểm trong đồ thị."
            return self._result(
                path=[],
                visited_order=visited_order,
                steps=steps,
                explanation=self._explanation([], rule),
                graph=graph,
                edge_lookup=edge_lookup,
                enable_logging=enable_logging,
            )

        path = reconstruct_path(parent, goal)
        rule = (
            "DFS luôn đi theo nhánh được nạp sau cùng (LIFO), nên đường tìm thấy "
            "không nhất thiết là đường ngắn nhất."
        )
        return self._result(
            path=path,
            visited_order=visited_order,
            steps=steps,
            explanation=self._explanation(path, rule),
            graph=graph,
            edge_lookup=edge_lookup,
            enable_logging=enable_logging,
        )


class MockUCS(_MockBase):
    """Uniform-Cost Search (priority queue, relaxation) — mock (GUI § 6)."""

    name = "ucs"

    def search(
        self,
        graph: GraphLike,
        start: str,
        goal: str,
        *,
        enable_logging: bool = True,
    ) -> SearchResult:
        early = self._early(
            graph=graph,
            start=start,
            goal=goal,
            start_equals_goal=start == goal,
        )
        if early is not None:
            return early

        adjacency, edge_lookup = self._setup(graph)
        parent: dict[str, str | None] = {start: None}
        best_cost: dict[str, float] = {start: 0.0}
        closed: set[str] = set()
        counter = 0
        heap: list[tuple[float, int, str]] = [(0.0, counter, start)]
        visited_order: list[str] = []
        steps: list[SearchStep] = []
        found = False

        def frontier_ids() -> list[str]:
            return [node for _, _, node in heap]

        while heap:
            cost, _, current = heappop(heap)
            if current in closed:
                continue
            if cost != best_cost.get(current):
                continue  # stale entry (lazy deletion)
            visited_order.append(current)
            if current == goal:
                if enable_logging:
                    steps.append(
                        SearchStep(
                            current_node=current,
                            frontier=[],
                            reason="UCS - mô phỏng: đạt node đích với chi phí nhỏ nhất.",
                        )
                    )
                found = True
                break
            if enable_logging:
                steps.append(
                    SearchStep(
                        current_node=current,
                        frontier=frontier_ids(),
                        reason="UCS - mô phỏng: mở rộng node có chi phí nhỏ nhất.",
                    )
                )
            closed.add(current)
            for neighbor in adjacency.get(current, ()):
                if neighbor in closed:
                    continue
                new_cost = cost + edge_cost(edge_lookup[(current, neighbor)])
                if new_cost < best_cost.get(neighbor, float("inf")):
                    best_cost[neighbor] = new_cost
                    parent[neighbor] = current
                    counter += 1
                    heappush(heap, (new_cost, counter, neighbor))

        if not found:
            rule = "Không tồn tại đường đi giữa hai điểm trong đồ thị."
            return self._result(
                path=[],
                visited_order=visited_order,
                steps=steps,
                explanation=self._explanation([], rule),
                graph=graph,
                edge_lookup=edge_lookup,
                enable_logging=enable_logging,
            )

        path = reconstruct_path(parent, goal)
        rule = (
            "UCS mở rộng node theo chi phí cộng dồn nhỏ nhất (priority queue), "
            "nên đường tìm thấy là đường tối ưu theo tổng chi phí."
        )
        return self._result(
            path=path,
            visited_order=visited_order,
            steps=steps,
            explanation=self._explanation(path, rule),
            graph=graph,
            edge_lookup=edge_lookup,
            enable_logging=enable_logging,
        )


class _MockHeuristic(_MockBase):
    """Shared heuristic machinery (coordinates + admissible h for Greedy/A*)."""

    @staticmethod
    def _coords(graph: GraphLike) -> dict[str, tuple[float, float]]:
        return {node.id: (node.latitude, node.longitude) for node in graph.nodes}

    def _h(self, node: str, goal: str, coords: dict[str, tuple[float, float]]) -> float:
        """Admissible estimate: alpha * straight-line km to the goal.

        Scaled by ``weights.distance`` so it is a lower bound on the § 14
        combined cost (all other cost terms are >= 0), keeping A* optimal.
        """
        meters = haversine_m(coords[node], coords[goal])
        return DEFAULT_WEIGHTS.distance * (meters / 1000.0)


class MockGreedy(_MockHeuristic):
    """Greedy Best-First Search (open on h) — mock (GUI § 6)."""

    name = "greedy"

    def search(
        self,
        graph: GraphLike,
        start: str,
        goal: str,
        *,
        enable_logging: bool = True,
    ) -> SearchResult:
        early = self._early(
            graph=graph,
            start=start,
            goal=goal,
            start_equals_goal=start == goal,
        )
        if early is not None:
            return early

        adjacency, edge_lookup = self._setup(graph)
        coords = self._coords(graph)
        parent: dict[str, str | None] = {start: None}
        best_h: dict[str, float] = {start: self._h(start, goal, coords)}
        closed: set[str] = set()
        counter = 0
        heap: list[tuple[float, int, str]] = [(best_h[start], counter, start)]
        visited_order: list[str] = []
        steps: list[SearchStep] = []
        found = False

        while heap:
            h, _, current = heappop(heap)
            if current in closed:
                continue
            if h != best_h.get(current):
                continue  # stale entry
            visited_order.append(current)
            if current == goal:
                if enable_logging:
                    steps.append(
                        SearchStep(
                            current_node=current,
                            frontier=[],
                            reason="Greedy - mô phỏng: đạt node đích.",
                        )
                    )
                found = True
                break
            if enable_logging:
                steps.append(
                    SearchStep(
                        current_node=current,
                        frontier=[node for _, _, node in heap],
                        reason="Greedy - mô phỏng: mở rộng node gần đích nhất (heuristic).",
                    )
                )
            closed.add(current)
            for neighbor in adjacency.get(current, ()):
                if neighbor in closed:
                    continue
                hv = self._h(neighbor, goal, coords)
                if hv < best_h.get(neighbor, float("inf")):
                    best_h[neighbor] = hv
                    parent[neighbor] = current
                    counter += 1
                    heappush(heap, (hv, counter, neighbor))

        if not found:
            rule = "Không tồn tại đường đi giữa hai điểm trong đồ thị."
            return self._result(
                path=[],
                visited_order=visited_order,
                steps=steps,
                explanation=self._explanation([], rule),
                graph=graph,
                edge_lookup=edge_lookup,
                enable_logging=enable_logging,
            )

        path = reconstruct_path(parent, goal)
        rule = (
            "Greedy chỉ mở rộng node có heuristic nhỏ nhất (gần đích theo "
            "đường chim bay), nên đường tìm thấy có thể không tối ưu về tổng chi phí."
        )
        return self._result(
            path=path,
            visited_order=visited_order,
            steps=steps,
            explanation=self._explanation(path, rule),
            graph=graph,
            edge_lookup=edge_lookup,
            enable_logging=enable_logging,
        )


class MockAstar(_MockHeuristic):
    """A* Search (open on f = g + h) — mock (GUI § 6)."""

    name = "astar"

    def search(
        self,
        graph: GraphLike,
        start: str,
        goal: str,
        *,
        enable_logging: bool = True,
    ) -> SearchResult:
        early = self._early(
            graph=graph,
            start=start,
            goal=goal,
            start_equals_goal=start == goal,
        )
        if early is not None:
            return early

        adjacency, edge_lookup = self._setup(graph)
        coords = self._coords(graph)
        parent: dict[str, str | None] = {start: None}
        g_score: dict[str, float] = {start: 0.0}
        closed: set[str] = set()
        counter = 0
        start_f = self._h(start, goal, coords)
        heap: list[tuple[float, int, str]] = [(start_f, counter, start)]
        visited_order: list[str] = []
        steps: list[SearchStep] = []
        found = False

        while heap:
            f, _, current = heappop(heap)
            if current in closed:
                continue
            if f != g_score.get(current) + self._h(current, goal, coords):
                continue  # stale entry
            visited_order.append(current)
            if current == goal:
                if enable_logging:
                    steps.append(
                        SearchStep(
                            current_node=current,
                            frontier=[],
                            reason="A* - mô phỏng: đạt node đích với chi phí tối ưu.",
                        )
                    )
                found = True
                break
            if enable_logging:
                frontier = []
                seen: set[str] = set()
                for _, _, node in heap:
                    if node not in seen:
                        seen.add(node)
                        frontier.append(node)
                steps.append(
                    SearchStep(
                        current_node=current,
                        frontier=frontier,
                        reason="A* - mô phỏng: mở rộng node có f = g + h nhỏ nhất.",
                    )
                )
            closed.add(current)
            for neighbor in adjacency.get(current, ()):
                if neighbor in closed:
                    continue
                tentative = g_score[current] + edge_cost(edge_lookup[(current, neighbor)])
                if tentative < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = tentative
                    parent[neighbor] = current
                    counter += 1
                    heappush(heap, (tentative + self._h(neighbor, goal, coords), counter, neighbor))

        if not found:
            rule = "Không tồn tại đường đi giữa hai điểm trong đồ thị."
            return self._result(
                path=[],
                visited_order=visited_order,
                steps=steps,
                explanation=self._explanation([], rule),
                graph=graph,
                edge_lookup=edge_lookup,
                enable_logging=enable_logging,
            )

        path = reconstruct_path(parent, goal)
        rule = (
            "A* mở rộng node có f = g + h nhỏ nhất với heuristic chấp nhận được "
            "(chặn dưới), nên đường tìm thấy là tối ưu theo tổng chi phí."
        )
        return self._result(
            path=path,
            visited_order=visited_order,
            steps=steps,
            explanation=self._explanation(path, rule),
            graph=graph,
            edge_lookup=edge_lookup,
            enable_logging=enable_logging,
        )


def reconstruct_path(parent: dict[str, str | None], goal: str) -> list[str]:
    """Rebuild the start->goal node list from a predecessor map."""
    path: list[str] = []
    node: str | None = goal
    while node is not None:
        path.append(node)
        node = parent.get(node)
    path.reverse()
    return path
