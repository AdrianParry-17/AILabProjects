"""Versioned HTTP request/response contract for the React client."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .costs import CostWeights


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AlgorithmName(str, Enum):
    BFS = "bfs"
    DFS = "dfs"
    UCS = "ucs"
    DIJKSTRA = "dijkstra"
    ASTAR = "astar"
    GREEDY_BEST_FIRST = "greedy_best_first"
    BIDIRECTIONAL_DIJKSTRA = "bidirectional_dijkstra"
    IDA_STAR = "ida_star"


class HeuristicName(str, Enum):
    ZERO = "zero"
    HAVERSINE = "haversine"
    TRAVEL_TIME = "travel_time"
    TRAFFIC_AWARE = "traffic_aware"


class ScenarioName(str, Enum):
    NORMAL = "normal"
    MORNING_RUSH = "morning_rush"
    EVENING_RUSH = "evening_rush"
    HEAVY_RAIN = "heavy_rain"
    INCIDENT = "incident"


class MultiRouteMethod(str, Enum):
    NEAREST_NEIGHBOR = "nearest_neighbor"
    HELD_KARP = "held_karp"
    TWO_OPT = "two_opt"
    SIMULATED_ANNEALING = "simulated_annealing"


class CostWeightsRequest(StrictModel):
    distance: float = Field(0.25, ge=0, le=100)
    travel_time: float = Field(0.50, ge=0, le=100)
    traffic_delay: float = Field(0.20, ge=0, le=100)
    risk: float = Field(0.05, ge=0, le=100)

    @model_validator(mode="after")
    def require_positive_total(self) -> CostWeightsRequest:
        if self.distance + self.travel_time + self.traffic_delay + self.risk <= 0:
            raise ValueError("At least one cost weight must be positive")
        return self

    def to_domain(self) -> CostWeights:
        return CostWeights(**self.model_dump())


def _default_cost_weights() -> CostWeightsRequest:
    return CostWeightsRequest(
        distance=0.25,
        travel_time=0.50,
        traffic_delay=0.20,
        risk=0.05,
    )


class SearchRequest(StrictModel):
    start_id: str = Field(min_length=1, max_length=128)
    goal_id: str = Field(min_length=1, max_length=128)
    algorithm: AlgorithmName = AlgorithmName.ASTAR
    heuristic: HeuristicName = HeuristicName.TRAVEL_TIME
    scenario: ScenarioName = ScenarioName.NORMAL
    cost_weights: CostWeightsRequest = Field(default_factory=_default_cost_weights)
    include_trace: bool = True
    max_trace_events: int = Field(1_000, ge=0, le=10_000)
    max_expansions: int = Field(100_000, ge=1, le=1_000_000)
    include_alternative: bool = True


class CompareRequest(StrictModel):
    start_id: str = Field(min_length=1, max_length=128)
    goal_id: str = Field(min_length=1, max_length=128)
    algorithms: list[AlgorithmName] = Field(
        default_factory=lambda: [
            AlgorithmName.BFS,
            AlgorithmName.UCS,
            AlgorithmName.ASTAR,
            AlgorithmName.GREEDY_BEST_FIRST,
            AlgorithmName.BIDIRECTIONAL_DIJKSTRA,
        ],
        min_length=2,
        max_length=8,
    )
    heuristic: HeuristicName = HeuristicName.TRAVEL_TIME
    scenario: ScenarioName = ScenarioName.NORMAL
    cost_weights: CostWeightsRequest = Field(default_factory=_default_cost_weights)
    include_trace: bool = False
    max_trace_events: int = Field(300, ge=0, le=2_000)
    max_expansions: int = Field(100_000, ge=1, le=1_000_000)

    @model_validator(mode="after")
    def algorithms_must_be_unique(self) -> CompareRequest:
        if len(set(self.algorithms)) != len(self.algorithms):
            raise ValueError("algorithms must not contain duplicates")
        return self


class MultiRouteRequest(StrictModel):
    start_id: str = Field(min_length=1, max_length=128)
    stop_ids: list[str] = Field(min_length=1, max_length=12)
    method: MultiRouteMethod = MultiRouteMethod.NEAREST_NEIGHBOR
    return_to_start: bool = False
    scenario: ScenarioName = ScenarioName.NORMAL
    cost_weights: CostWeightsRequest = Field(default_factory=_default_cost_weights)
    seed: int = Field(42, ge=0, le=2_147_483_647)
    max_iterations: int = Field(1_000, ge=1, le=100_000)
    max_expansions: int = Field(100_000, ge=1, le=1_000_000)

    @model_validator(mode="after")
    def validate_stops(self) -> MultiRouteRequest:
        if any(not stop.strip() for stop in self.stop_ids):
            raise ValueError("stop_ids cannot contain empty values")
        if len(set(self.stop_ids)) != len(self.stop_ids):
            raise ValueError("stop_ids must be unique")
        if self.start_id in self.stop_ids:
            raise ValueError("stop_ids must not contain start_id")
        if self.method == MultiRouteMethod.HELD_KARP and len(self.stop_ids) > 10:
            raise ValueError("held_karp accepts at most 10 stops")
        return self


class DatasetMetadataResponse(BaseModel):
    id: str
    name: str
    city: str
    country: str
    version: str
    source: str
    description: str
    generated_at: str | None = None
    disclaimer: str | None = None
    source_url: str | None = None
    license: str | None = None
    attribution: str | None = None
    osm_base_timestamp: str | None = None
    overpass_query: str | None = None
    network_filter: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    stats: dict[str, Any] = Field(default_factory=dict)


class BoundingBox(BaseModel):
    south: float
    west: float
    north: float
    east: float


class GraphSummary(BaseModel):
    node_count: int
    directed_edge_count: int
    distance_lower_bound_scale: float
    max_speed_kph: float
    bounding_box: BoundingBox


class ScenarioMetadata(BaseModel):
    id: str
    label: str
    description: str
    base_multiplier: float
    jitter: float


class AlgorithmMetadataResponse(BaseModel):
    id: str
    label: str
    family: str
    weighted: bool
    heuristic_required: bool
    complete: bool
    optimality: str
    description: str


class HeuristicMetadataResponse(BaseModel):
    id: str
    label: str
    description: str
    admissible: bool
    consistent: bool
    warning: str | None = None
    used: bool | None = None


class MultiMethodMetadataResponse(BaseModel):
    id: str
    label: str
    exact: bool
    max_recommended_stops: int
    description: str


class GraphNodeResponse(BaseModel):
    id: str
    name: str
    kind: str
    lat: float
    lon: float
    attributes: dict[str, Any] = Field(default_factory=dict)


class TrafficStatusResponse(BaseModel):
    edge_id: str
    scenario: str
    multiplier: float
    effective_speed_kph: float
    free_flow_time_s: float
    travel_time_s: float | None
    delay_s: float | None
    congestion: str
    closed: bool
    reason: str


class TrafficOverlayEdgeResponse(BaseModel):
    edge_id: str
    multiplier: float
    effective_speed_kph: float
    travel_time_s: float | None
    congestion: str
    closed: bool


class TrafficOverlayResponse(BaseModel):
    scenario: ScenarioMetadata
    edges: list[TrafficOverlayEdgeResponse]


class DirectedEdgeResponse(BaseModel):
    id: str
    source: str
    target: str
    distance_m: float
    speed_kph: float
    road_name: str
    road_class: str
    risk: float
    traversable: bool
    direction: Literal["one-way", "two-way", "directed"]
    attributes: dict[str, Any] = Field(default_factory=dict)
    geometry: list[list[float]]
    traffic: TrafficStatusResponse


class GraphGeoJSONFeature(BaseModel):
    type: Literal["Feature"]
    id: str
    properties: dict[str, Any]
    geometry: RouteGeoJSON


class GraphGeoJSONFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[GraphGeoJSONFeature]


class GraphResponse(BaseModel):
    dataset: DatasetMetadataResponse
    summary: GraphSummary
    scenario: ScenarioMetadata
    nodes: list[GraphNodeResponse]
    directed_edges: list[DirectedEdgeResponse]
    graph_geojson: GraphGeoJSONFeatureCollection


class RouteGeoJSON(BaseModel):
    type: Literal["LineString"]
    coordinates: list[list[float]]


class TraceEventResponse(BaseModel):
    step: int
    event: str
    node_id: str | None = None
    parent_id: str | None = None
    edge_id: str | None = None
    direction: Literal["forward", "backward"]
    frontier_size: int
    explored_count: int
    g_cost: float | None = None
    h_cost: float | None = None
    f_cost: float | None = None
    depth: int | None = None
    message: str


class TraceResponse(BaseModel):
    schema_version: str
    event_count: int
    truncated: bool
    events: list[TraceEventResponse]


class SearchMetricsResponse(BaseModel):
    runtime_ms: float
    visited_nodes: int
    expanded_nodes: int
    generated_nodes: int
    frontier_peak: int
    heuristic_calls: int
    path_nodes: int
    path_edges: int
    hop_count: int
    path_cost: float | None
    trace_truncated: bool
    distance_m: float = 0
    free_flow_time_s: float = 0
    travel_time_s: float = 0
    traffic_delay_s: float = 0
    risk_exposure: float = 0


class CostBreakdownResponse(BaseModel):
    weights: dict[str, float]
    units: dict[str, str]
    edge_count: int
    distance_m: float
    free_flow_time_s: float
    travel_time_s: float
    traffic_delay_s: float
    risk_exposure: float
    components: dict[str, float]
    total_cost: float


class ExplanationResponse(BaseModel):
    summary: str
    optimality: str
    heuristic_note: str
    traffic_note: str
    cost_model: str
    warnings: list[str]


class AlternativeRouteResponse(BaseModel):
    algorithm: str
    reason: str
    path: list[str]
    edge_ids: list[str]
    route_geojson: RouteGeoJSON
    difference_percent: float | None
    metrics: SearchMetricsResponse
    cost_breakdown: CostBreakdownResponse


class SearchResponse(BaseModel):
    request_id: str
    status: Literal["found", "unreachable", "limit_reached"]
    found: bool
    start_id: str
    goal_id: str
    algorithm: AlgorithmMetadataResponse
    heuristic: HeuristicMetadataResponse
    scenario: ScenarioMetadata
    path: list[str]
    edge_ids: list[str]
    route_geojson: RouteGeoJSON | None
    metrics: SearchMetricsResponse
    trace: TraceResponse
    explanation: ExplanationResponse
    alternative: AlternativeRouteResponse | None
    cost_breakdown: CostBreakdownResponse


class CompareRankingResponse(BaseModel):
    rank: int
    algorithm: str
    found: bool
    path_cost: float | None
    expanded_nodes: int
    runtime_ms: float


class PathGroupResponse(BaseModel):
    edge_ids: list[str]
    algorithms: list[str]


class ComparisonAgreementResponse(BaseModel):
    all_found: bool
    same_path: bool
    unique_path_count: int
    path_groups: list[PathGroupResponse]


class CompareResponse(BaseModel):
    request_id: str
    start_id: str
    goal_id: str
    scenario: ScenarioMetadata
    runs: list[SearchResponse]
    ranking: list[CompareRankingResponse]
    best_algorithm: str | None
    agreement: ComparisonAgreementResponse


class MultiRouteSegmentResponse(BaseModel):
    from_id: str
    to_id: str
    path: list[str]
    edge_ids: list[str]
    route_geojson: RouteGeoJSON
    cost_breakdown: CostBreakdownResponse


class MultiRouteMetricsResponse(BaseModel):
    runtime_ms: float
    pairwise_searches: int
    pairwise_expanded_nodes: int
    optimizer_iterations: int
    optimizer_improvements: int
    stop_count: int
    hop_count: int
    path_cost: float
    distance_m: float
    travel_time_s: float
    traffic_delay_s: float


class MultiRouteResponse(BaseModel):
    request_id: str
    status: Literal["found"]
    method: MultiMethodMetadataResponse
    scenario: ScenarioMetadata
    start_id: str
    requested_stop_ids: list[str]
    stop_order: list[str]
    return_to_start: bool
    visit_sequence: list[str]
    path: list[str]
    edge_ids: list[str]
    route_geojson: RouteGeoJSON
    segments: list[MultiRouteSegmentResponse]
    metrics: MultiRouteMetricsResponse
    cost_breakdown: CostBreakdownResponse
    explanation: ExplanationResponse


class MetadataResponse(BaseModel):
    api: dict[str, str]
    dataset: DatasetMetadataResponse
    graph: GraphSummary
    algorithms: list[AlgorithmMetadataResponse]
    heuristics: list[HeuristicMetadataResponse]
    scenarios: list[ScenarioMetadata]
    multi_route_methods: list[MultiMethodMetadataResponse]
    defaults: dict[str, Any]
    trace_schema: dict[str, Any]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    dataset_id: str
    dataset_version: str
    node_count: int
    directed_edge_count: int
