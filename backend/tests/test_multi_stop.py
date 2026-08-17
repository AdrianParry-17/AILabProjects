from __future__ import annotations

from app.multi_stop import optimize_stop_order


def sample_matrix():
    points = ["s", "a", "b", "c"]
    matrix = {(point, point): 0 for point in points}
    matrix.update(
        {
            ("s", "a"): 1, ("s", "b"): 4, ("s", "c"): 7,
            ("a", "s"): 1, ("a", "b"): 1, ("a", "c"): 5,
            ("b", "s"): 4, ("b", "a"): 1, ("b", "c"): 1,
            ("c", "s"): 7, ("c", "a"): 5, ("c", "b"): 1,
        }
    )
    return matrix


def test_held_karp_is_no_worse_than_greedy():
    matrix = sample_matrix()
    greedy = optimize_stop_order("nearest_neighbor", "s", ["a", "b", "c"], matrix, True)
    exact = optimize_stop_order("held_karp", "s", ["a", "b", "c"], matrix, True)
    assert exact.total_cost <= greedy.total_cost
    assert sorted(exact.order) == ["a", "b", "c"]
    assert exact.exact


def test_seeded_annealing_is_reproducible():
    matrix = sample_matrix()
    first = optimize_stop_order(
        "simulated_annealing", "s", ["a", "b", "c"], matrix, True,
        seed=123, max_iterations=100,
    )
    second = optimize_stop_order(
        "simulated_annealing", "s", ["a", "b", "c"], matrix, True,
        seed=123, max_iterations=100,
    )
    assert first.order == second.order
    assert first.total_cost == second.total_cost

