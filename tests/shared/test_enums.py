"""shared/enums unit tests (AlgorithmName)."""

from __future__ import annotations

from shared.enums import AlgorithmName


def test_greedy_value() -> None:
    assert AlgorithmName.GREEDY.value == "greedy"


def test_algorithm_name_is_additive_and_unchanged() -> None:
    """Every existing members' value survives; GREEDY is added exactly once."""
    assert {member.value for member in AlgorithmName} == {
        "bfs",
        "dfs",
        "ucs",
        "astar",
        "dijkstra",
        "ida_star",
        "greedy",
    }


def test_algorithm_name_values_are_unique() -> None:
    values = [member.value for member in AlgorithmName]
    assert len(values) == len(set(values))