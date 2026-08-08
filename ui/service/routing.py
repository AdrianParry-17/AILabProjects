"""Route expansion + single-algorithm routing for the GUI service.

`run` delegates to the core algorithm registry via ``run_algorithm`` and
returns a ``(SearchResult, source)`` pair where ``source`` is ``"real"`` for the
real backend (no mock). `expand_path` turns a list of POI ids into a GeoJSON
LineString Feature using ``delivery.route.expand_poi_path``; it returns ``None``
when there is nothing to expand.
"""

from __future__ import annotations

from typing import Any

import algorithms  # noqa: F401 - register algorithms into the core registry
from core.search_algorithm import run_algorithm
from core.search_result import SearchResult
from delivery.models import DeliveryGraph
from delivery.road import RoadGraph
from delivery.route import expand_poi_path
from shared.logger import get_logger

from . import graphs

__all__ = ["expand_path", "run"]

logger = get_logger(__name__)


def run(
    name: str,
    start: str,
    goal: str,
    *,
    enable_logging: bool = True,
) -> tuple[SearchResult, str]:
    """Run a single registered algorithm on the real road graph.

    Args:
        name: registered algorithm name (e.g. ``"bfs"``).
        start: start node id.
        goal: goal node id.
        enable_logging: forward to the algorithm (e.g. per-step logging);
            on by default so interactive searches animate + replay.


    Returns:
        ``(result, "real")`` — the ``"real"`` source distinguishes backend runs
        from the mock transport at the HTTP layer.

    Raises:
        KeyError: when ``name`` is not registered.
    """
    logger.debug("running real search %s %s -> %s", name, start, goal)
    delivery_graph = graphs.get_delivery_graph()
    result = run_algorithm(name, delivery_graph, start, goal, enable_logging=enable_logging)
    return result, "real"


def expand_path(
    path: list[str],
    road_graph: RoadGraph | None = None,
    delivery_graph: DeliveryGraph | None = None,
) -> dict[str, Any] | None:
    """Expand a list of POI node ids into a GeoJSON LineString Feature.

    Args:
        path: ordered delivery node ids (a partial or full route).
        road_graph: road graph used to fill any hop without delivery geometry.
        delivery_graph: delivery graph whose edges carry ``road_path`` geometry.

    Returns:
        A ``Feature`` with a ``LineString`` geometry of ``[lon, lat]``
        coordinates, or ``None`` when ``path`` has fewer than two ids.

    Raises:
        ValueError / KeyError: propagated from ``expand_poi_path`` when a hop
        cannot be expanded (never swallowed).
    """
    if not path or len(path) < 2:
        return None
    expanded = expand_poi_path(path, road_graph, delivery_graph)
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": expanded.geometry,
        },
    }