"""Delivery Graph: the application-layer POI graph for the AI search lab.

Two-layer architecture:

* Road Graph  (data/processed/graph.json, data.models.GraphData): all OSM intersections/roads.
  Used only for shortest-path computation between POIs.
* Delivery Graph (data/exports/delivery_graph.json, this package): only meaningful delivery POIs.
  Search algorithms, UI, animation and reports operate on this graph.

Each DeliveryEdge carries the detailed road path (road_path + geometry) it was derived
from, so the UI can expand a POI-level route into a street-level route for display.
"""

from .builder import build_delivery_graph
from .loader import load_delivery_graph, load_delivery_metadata
from .models import DeliveryEdge, DeliveryGraph, DeliveryNode
from .road import RoadGraph, RoadPath
from .route import expand_poi_path

__all__ = [
    "DeliveryEdge",
    "DeliveryGraph",
    "DeliveryNode",
    "RoadGraph",
    "RoadPath",
    "build_delivery_graph",
    "expand_poi_path",
    "load_delivery_graph",
    "load_delivery_metadata",
]
