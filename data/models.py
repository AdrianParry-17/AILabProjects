"""Shared Pydantic models for graph.json."""

from pydantic import BaseModel, Field

from config.settings import SCHEMA_VERSION

__all__ = ["SCHEMA_VERSION", "Edge", "GraphData", "Node"]


class Node(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    kind: str = "intersection"
    attributes: dict = Field(default_factory=dict)


class Edge(BaseModel):
    start: str
    end: str
    distance_km: float = Field(ge=0)
    time_min: float = Field(ge=0)
    congestion: float = Field(ge=0)
    risk: float = Field(ge=0)
    direction: str
    road_name: str = ""
    road_class: str = ""
    attributes: dict = Field(default_factory=dict)


class GraphData(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
