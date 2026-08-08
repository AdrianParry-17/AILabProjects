/**
 * DTO types mirroring the GUI service contract (docs/GUI_ROADMAP.md §11 and
 * docs/MAP_CONTRACT.md). Field names MUST stay snake_case and match the JSON
 * exactly; do not rename to camelCase.
 */

export interface DeliveryNode {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  kind: string;
  attributes: Record<string, unknown>;
}

export interface DeliveryEdge {
  edge_id: string;
  start: string;
  end: string;
  distance_km: number;
  time_min: number;
  congestion: number;
  risk: number;
  direction: string;
  road_path: string[];
  road_name: string;
  road_class: string;
  attributes: Record<string, unknown>;
}

export interface GraphGeojson {
  type: "FeatureCollection";
  features: unknown[];
}

export interface GraphResponse {
  graph: {
    nodes: DeliveryNode[];
    edges: DeliveryEdge[];
    geojson: GraphGeojson;
  };
  bbox: [number, number, number, number];
  metadata: {
    schema_version: string;
    node_count: number;
    edge_count: number;
  };
}

export interface HealthResponse {
  status: "ok";
}

/** One `SearchStep` frame (MAP_CONTRACT.md §3.2). */
export interface SearchStep {
  current_node: string;
  frontier: string[];
  reason: string;
}

/** The §11 `result` object, mirroring `SearchResult` field names. */
export interface SearchResult {
  path: string[];
  visited_nodes: string[];
  steps: SearchStep[];
  total_distance_km: number;
  total_time_min: number;
  total_cost: number;
  processing_time_ms: number;
  explanation: string;
}

/** The §11 `metrics` object (front-end derived values + verbatim totals). */
export interface SearchMetrics {
  hops: number;
  nodes_visited: number;
  distance_km: number;
  time_min: number;
  cost: number;
  processing_time_ms: number;
}

/** A GeoJSON LineString Feature (the expanded route, §4/MAP_CONTRACT). */
export interface RouteFeature {
  type: "Feature";
  geometry: {
    type: "LineString";
    coordinates: number[][];
  };
}

/** The §11 `POST /search` response body. */
export interface SearchResponse {
  run: {
    id: string;
    algorithm: string;
    source: string;
  };
  result: SearchResult;
  metrics: SearchMetrics;
  route: RouteFeature | null;
}

/** One entry of `GET /algorithms` (GUI_ROADMAP.md §11). */
export interface AlgorithmSummary {
  id: string;
  label: string;
  mock: boolean;
}

/** The `GET /algorithms` response body (GUI_ROADMAP.md §11). */
export interface AlgorithmsResponse {
  algorithms: AlgorithmSummary[];
}

/** One recorded run of `GET /history` (GUI_ROADMAP.md §11). */
export interface HistoryRun {
  id: string;
  algorithm: string;
  start: string;
  goal: string;
  source: string;
  created_at: string;
  hops: number;
}

/** The `GET /history` response body (GUI_ROADMAP.md §11). */
export interface HistoryResponse {
  runs: HistoryRun[];
}

/** The `GET /version` body. */
export interface VersionResponse {
  service: string;
  version: string;
  api_version: string;
}

/**
 * §7 error envelope: {"error": {"code", "message", "details"}}.
 * Both transports surface failures as this shape.
 */
export interface ErrorEnvelope {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}