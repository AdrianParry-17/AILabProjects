"""Pydantic models for the application-layer Delivery Graph."""

from pydantic import BaseModel, Field

from config.settings import SCHEMA_VERSION

__all__ = ["SCHEMA_VERSION", "DeliveryEdge", "DeliveryGraph", "DeliveryNode"]


class DeliveryNode(BaseModel):
    """A meaningful delivery point (market, supermarket, bus station, hospital, ...).

    Mirrors `data.models.Node` so both graph layers share the same id scheme.
    """

    id: str
    name: str
    latitude: float
    longitude: float
    kind: str
    attributes: dict = Field(default_factory=dict)


class DeliveryEdge(BaseModel):
    """An abstract edge between two delivery POIs.

    Its metrics equal the detailed Road Graph shortest-path between the two POIs. The
    concrete street-level route is retained in `road_path` (road node ids) and
    `attributes["geometry"]` ([lon, lat] polyline) so a POI-level route can be expanded
    for map display.
    """

    edge_id: str = ""
    start: str
    end: str
    distance_km: float = Field(ge=0)
    time_min: float = Field(ge=0)
    congestion: float = Field(ge=0)
    risk: float = Field(ge=0)
    direction: str = "two-way"
    road_path: list[str] = Field(default_factory=list)
    road_name: str = ""
    road_class: str = ""
    attributes: dict = Field(default_factory=dict)


class DeliveryGraph(BaseModel):
    metadata: dict = Field(default_factory=dict)
    nodes: list[DeliveryNode]
    edges: list[DeliveryEdge]