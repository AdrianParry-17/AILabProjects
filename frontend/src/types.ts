export type PlannerMode = "route" | "multi" | "compare" | "learn";
export type TrafficScenario = "normal" | "rush_hour" | "rain" | "flood" | "night" | string;
export type Objective = "balanced" | "distance" | "time" | "safety" | "priority_delivery" | string;

export interface CostWeights {
  distance: number;
  time: number;
  congestion: number;
  risk: number;
}

export interface GraphNode {
  id: string;
  name: string;
  short_name?: string;
  kind: string;
  lat: number;
  lon: number;
  district?: string;
  address?: string;
  is_delivery_point?: boolean;
  poi_category?: string;
  routing_component?: "primary" | "peripheral" | string;
  tags?: Record<string, string | number | boolean>;
}

export interface GraphEdge {
  id?: string;
  source: string;
  target: string;
  name: string;
  road_type: string;
  distance_m: number;
  estimated_time_min?: number;
  travel_time_min?: number;
  congestion: number;
  risk: number;
  direction?: "one_way" | "two_way" | string;
  oneway?: boolean;
  closed?: boolean;
  traversable?: boolean;
  speed_kph?: number;
  flags?: string[];
  geometry?: [number, number][];
}

export interface GraphPayload {
  name: string;
  city: string;
  description?: string;
  source?: string;
  generated_at?: string;
  center?: { lat: number; lon: number };
  bounds?: [[number, number], [number, number]];
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats?: Record<string, number | string>;
  scenario?: TrafficScenario;
}

export interface AlgorithmMeta {
  id: string;
  name: string;
  family?: string;
  description: string;
  complete: boolean | string;
  optimal: boolean | string;
  weighted?: boolean;
  supports_heuristic?: boolean;
  complexity_time?: string;
  complexity_space?: string;
  caveat?: string;
}

export interface HeuristicMeta {
  id: string;
  name: string;
  description: string;
  admissible: boolean | string;
  consistent: boolean | string;
  best_for?: string;
  warning?: string;
}

export interface OptionMeta {
  id: string;
  name: string;
  description?: string;
  color?: string;
  weights?: CostWeights;
}

export interface MetadataPayload {
  algorithms: AlgorithmMeta[];
  heuristics: HeuristicMeta[];
  objectives: OptionMeta[];
  scenarios: OptionMeta[];
  multi_algorithms?: AlgorithmMeta[];
  defaults?: {
    algorithm?: string;
    heuristic?: string;
    objective?: string;
    scenario?: string;
    weights?: CostWeights;
  };
  dataset?: Record<string, string | number>;
}

export interface TraceStep {
  step: number;
  current: string;
  current_name?: string;
  phase?: "start" | "expand" | "iteration" | "finish";
  is_complete?: boolean;
  trace_truncated?: boolean;
  found?: boolean;
  parent_id?: string;
  active_edge_id?: string;
  explored_edge_ids?: string[];
  frontier_edge_ids?: string[];
  active_link?: TraceLink;
  explored_links?: TraceLink[];
  frontier_links?: TraceLink[];
  frontier: string[];
  frontier_names?: string[];
  visited: string[];
  explored?: string[];
  newly_discovered?: string[];
  frontier_size?: number;
  explored_count?: number;
  g_score?: number;
  h_score?: number;
  f_score?: number;
  depth?: number;
  reason: string;
  action?: string;
}

export interface TraceLink {
  source: string;
  target: string;
  edge_id?: string;
}

export interface RouteMetrics {
  total_distance_m: number;
  total_time_min: number;
  total_cost: number;
  explored_nodes: number;
  generated_nodes?: number;
  frontier_peak?: number;
  processing_time_ms: number;
  hop_count?: number;
  average_congestion?: number;
  risk_score?: number;
  memory_estimate_kb?: number;
}

export interface CostBreakdown {
  distance?: number;
  time?: number;
  congestion?: number;
  risk?: number;
  total?: number;
  [key: string]: number | undefined;
}

export interface RouteGeoJson {
  type: "Feature";
  properties?: Record<string, unknown>;
  geometry: {
    type: "LineString";
    coordinates: [number, number][];
  };
}

export interface SearchResponse {
  request_id?: string;
  found: boolean;
  algorithm: string;
  heuristic?: string;
  objective?: string;
  scenario?: string;
  path: string[];
  path_names?: string[];
  route_geojson?: RouteGeoJson;
  metrics: RouteMetrics;
  cost_breakdown?: CostBreakdown;
  trace: TraceStep[];
  explanation: string | { summary?: string; reasons?: string[]; warnings?: string[]; optimality?: string };
  alternative?: {
    label?: string;
    path: string[];
    path_names?: string[];
    metrics?: Partial<RouteMetrics>;
    explanation?: string;
    route_geojson?: RouteGeoJson;
  } | null;
  warnings?: string[];
  optimality?: string;
}

export interface SearchRequest {
  start: string;
  goal: string;
  algorithm: string;
  heuristic: string;
  objective: string;
  scenario: string;
  weights: CostWeights;
  avoid_flags?: string[];
  trace?: boolean;
}

export interface CompareResponse {
  results: SearchResponse[];
  winner?: string;
  insight?: string;
}

export interface MultiRouteResponse {
  found: boolean;
  method: string;
  order: string[];
  order_names?: string[];
  segments: MultiRouteSegment[];
  route_geojson?: RouteGeoJson;
  metrics: RouteMetrics;
  cost_breakdown?: CostBreakdown;
  explanation: string | { summary?: string; reasons?: string[]; warnings?: string[]; optimality?: string };
  optimality?: string;
  original_order?: string[];
  improvement_percent?: number;
}

export interface MultiRouteSegment {
  from_id: string;
  to_id: string;
  path: string[];
  edge_ids: string[];
  route_geojson?: RouteGeoJson;
  cost_breakdown?: CostBreakdown;
  distance_m?: number;
  travel_time_min?: number;
  total_cost?: number;
}
