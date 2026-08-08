"""Shared fixtures/helpers for the mock-algorithm invariant tests.

A tiny, deliberately-shaped micro graph exercises the § 6.6 invariants
independent of the delivery dataset. Nodes/edges are plain namespace objects
that satisfy ``shared.types.NodeLike`` / ``EdgeLike``.
"""

from __future__ import annotations

from types import SimpleNamespace


def node(node_id: str, lat: float, lon: float) -> SimpleNamespace:
    return SimpleNamespace(id=node_id, latitude=lat, longitude=lon)


def edge(start: str, end: str, *, distance_km=1.0, time_min=1.0, congestion=0.0, risk=0.0) -> SimpleNamespace:
    return SimpleNamespace(
        start=start,
        end=end,
        distance_km=distance_km,
        time_min=time_min,
        congestion=congestion,
        risk=risk,
    )


def micro_graph():
    """A deterministic micro graph exposing ``nodes`` / ``edges``.

    Directed layout (edge order defines the deterministic neighbor order):

        a -> b -> c -> d
        a -> e -> c
        z -> a          (only inbound; z is not reachable from a)
    """
    nodes = [
        node("a", 10.0, 106.0),
        node("b", 10.0, 106.1),
        node("c", 10.0, 106.2),
        node("d", 10.0, 106.3),
        node("e", 10.05, 106.15),
        node("z", 10.0, 106.9),
    ]
    edges = [
        edge("a", "b"),
        edge("b", "c"),
        edge("c", "d"),
        edge("a", "e"),
        edge("e", "c"),
        edge("z", "a"),
    ]
    return SimpleNamespace(nodes=nodes, edges=edges)
