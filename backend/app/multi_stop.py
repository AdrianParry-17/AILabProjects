"""Deterministic multi-stop route-order optimizers."""

from __future__ import annotations

import itertools
import math
import random
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MultiMethodMetadata:
    id: str
    label: str
    exact: bool
    max_recommended_stops: int
    description: str


MULTI_METHODS: dict[str, MultiMethodMetadata] = {
    "nearest_neighbor": MultiMethodMetadata(
        "nearest_neighbor", "Nearest Neighbor", False, 100,
        "Greedily visits the cheapest next stop; fast but order-dependent.",
    ),
    "held_karp": MultiMethodMetadata(
        "held_karp", "Held-Karp dynamic programming", True, 10,
        "Finds the exact minimum stop order in O(n²·2ⁿ) time and O(n·2ⁿ) memory.",
    ),
    "two_opt": MultiMethodMetadata(
        "two_opt", "Nearest Neighbor + 2-opt", False, 60,
        "Improves the greedy route by repeatedly reversing stop subsequences.",
    ),
    "simulated_annealing": MultiMethodMetadata(
        "simulated_annealing", "Seeded Simulated Annealing + 2-opt", False, 80,
        "Uses reproducible stochastic exploration, then deterministic 2-opt cleanup.",
    ),
}


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    method: str
    order: list[str]
    total_cost: float
    iterations: int
    improvements: int
    exact: bool


def multi_method_metadata() -> list[dict[str, Any]]:
    return [asdict(item) for item in MULTI_METHODS.values()]


def _route_cost(
    start: str,
    order: list[str],
    matrix: Mapping[tuple[str, str], float],
    return_to_start: bool,
) -> float:
    sequence = [start, *order]
    if return_to_start:
        sequence.append(start)
    return sum(matrix.get((a, b), math.inf) for a, b in itertools.pairwise(sequence))


def _nearest_neighbor(
    start: str,
    stops: list[str],
    matrix: Mapping[tuple[str, str], float],
    return_to_start: bool,
) -> OptimizationResult:
    current = start
    remaining = set(stops)
    order: list[str] = []
    while remaining:
        next_stop = min(remaining, key=lambda item: (matrix.get((current, item), math.inf), item))
        order.append(next_stop)
        remaining.remove(next_stop)
        current = next_stop
    return OptimizationResult(
        "nearest_neighbor", order, _route_cost(start, order, matrix, return_to_start),
        len(stops), 0, False,
    )


def _held_karp(
    start: str,
    stops: list[str],
    matrix: Mapping[tuple[str, str], float],
    return_to_start: bool,
) -> OptimizationResult:
    if len(stops) > MULTI_METHODS["held_karp"].max_recommended_stops:
        raise ValueError("Held-Karp is limited to at most 10 stops")
    if not stops:
        return OptimizationResult("held_karp", [], 0.0, 0, 0, True)

    # (visited mask, final stop index) -> (cost, predecessor index)
    dp: dict[tuple[int, int], tuple[float, int | None]] = {}
    for index, stop in enumerate(stops):
        dp[(1 << index, index)] = (matrix.get((start, stop), math.inf), None)

    transitions = 0
    full_mask = (1 << len(stops)) - 1
    for mask in range(1, full_mask + 1):
        for final in range(len(stops)):
            state = dp.get((mask, final))
            if state is None or not (mask & (1 << final)):
                continue
            current_cost = state[0]
            for candidate in range(len(stops)):
                if mask & (1 << candidate):
                    continue
                transitions += 1
                next_mask = mask | (1 << candidate)
                next_cost = current_cost + matrix.get((stops[final], stops[candidate]), math.inf)
                previous = dp.get((next_mask, candidate))
                if previous is None or next_cost < previous[0]:
                    dp[(next_mask, candidate)] = (next_cost, final)

    def final_cost(index: int) -> float:
        value = dp[(full_mask, index)][0]
        if return_to_start:
            value += matrix.get((stops[index], start), math.inf)
        return value

    last = min(range(len(stops)), key=lambda item: (final_cost(item), stops[item]))
    total = final_cost(last)
    reversed_order: list[str] = []
    mask = full_mask
    current: int | None = last
    while current is not None:
        reversed_order.append(stops[current])
        _, predecessor = dp[(mask, current)]
        mask ^= 1 << current
        current = predecessor
    reversed_order.reverse()
    return OptimizationResult("held_karp", reversed_order, total, transitions, 0, True)


def _two_opt_order(
    start: str,
    initial: list[str],
    matrix: Mapping[tuple[str, str], float],
    return_to_start: bool,
    max_iterations: int,
) -> tuple[list[str], float, int, int]:
    best = list(initial)
    best_cost = _route_cost(start, best, matrix, return_to_start)
    evaluations = 0
    improvements = 0
    changed = True
    while changed and evaluations < max_iterations:
        changed = False
        for left in range(len(best) - 1):
            for right in range(left + 1, len(best)):
                if evaluations >= max_iterations:
                    break
                evaluations += 1
                candidate = best[:left] + list(reversed(best[left : right + 1])) + best[right + 1 :]
                candidate_cost = _route_cost(start, candidate, matrix, return_to_start)
                if candidate_cost + 1e-12 < best_cost:
                    best, best_cost = candidate, candidate_cost
                    improvements += 1
                    changed = True
                    break
            if changed or evaluations >= max_iterations:
                break
    return best, best_cost, evaluations, improvements


def optimize_stop_order(
    method: str,
    start: str,
    stops: list[str],
    matrix: Mapping[tuple[str, str], float],
    return_to_start: bool,
    *,
    seed: int = 42,
    max_iterations: int = 1_000,
) -> OptimizationResult:
    if method not in MULTI_METHODS:
        choices = ", ".join(MULTI_METHODS)
        raise ValueError(f"Unknown multi-route method {method!r}; choose one of: {choices}")
    if method == "nearest_neighbor":
        return _nearest_neighbor(start, stops, matrix, return_to_start)
    if method == "held_karp":
        return _held_karp(start, stops, matrix, return_to_start)

    greedy = _nearest_neighbor(start, stops, matrix, return_to_start)
    if method == "two_opt":
        order, total, iterations, improvements = _two_opt_order(
            start, greedy.order, matrix, return_to_start, max_iterations
        )
        return OptimizationResult(method, order, total, iterations, improvements, False)

    rng = random.Random(seed)
    current = list(greedy.order)
    current_cost = greedy.total_cost
    best = list(current)
    best_cost = current_cost
    improvements = 0
    temperature = max(0.01, current_cost * 0.25 if math.isfinite(current_cost) else 1.0)
    iterations = 0
    while iterations < max_iterations and len(current) > 1:
        iterations += 1
        left, right = sorted(rng.sample(range(len(current)), 2))
        candidate = current[:left] + list(reversed(current[left : right + 1])) + current[right + 1 :]
        candidate_cost = _route_cost(start, candidate, matrix, return_to_start)
        delta = candidate_cost - current_cost
        if delta < 0 or rng.random() < math.exp(-delta / max(temperature, 1e-12)):
            current, current_cost = candidate, candidate_cost
            if current_cost + 1e-12 < best_cost:
                best, best_cost = list(current), current_cost
                improvements += 1
        temperature *= 0.995

    cleanup_budget = max(0, max_iterations - iterations)
    cleaned, cleaned_cost, evaluations, cleanup_improvements = _two_opt_order(
        start, best, matrix, return_to_start, cleanup_budget
    )
    return OptimizationResult(
        method,
        cleaned,
        cleaned_cost,
        iterations + evaluations,
        improvements + cleanup_improvements,
        False,
    )

