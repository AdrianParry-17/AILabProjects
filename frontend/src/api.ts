import type {
  AlgorithmMeta,
  CompareResponse,
  CostBreakdown,
  CostWeights,
  GraphPayload,
  HeuristicMeta,
  MetadataPayload,
  MultiRouteResponse,
  RouteGeoJson,
  RouteMetrics,
  SearchRequest,
  SearchResponse,
  TraceStep,
  TrafficScenario,
} from "./types";

const configuredBase = import.meta.env.VITE_API_BASE_URL as string | undefined;
export const API_BASE = (configuredBase || "/api/v1").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  detail?: unknown;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<T = unknown>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(init?.headers || {}),
    },
  });
  const contentType = response.headers.get("content-type") || "";
  const payload: any = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = payload?.error?.details ?? payload?.detail ?? payload;
    const message = payload?.error?.message || (typeof payload?.detail === "string" ? payload.detail : `API request failed (${response.status})`);
    throw new ApiError(message, response.status, detail);
  }
  return payload as T;
}

function toUiWeights(raw: any): CostWeights {
  return {
    distance: Number(raw?.distance ?? 1),
    time: Number(raw?.travel_time ?? raw?.time ?? 1.35),
    congestion: Number(raw?.traffic_delay ?? raw?.congestion ?? 2.2),
    risk: Number(raw?.risk ?? 3.4),
  };
}

function toApiWeights(weights: CostWeights) {
  return {
    distance: weights.distance,
    travel_time: weights.time,
    traffic_delay: weights.congestion,
    risk: weights.risk,
  };
}

function normalizeMetadata(raw: any): MetadataPayload {
  const algorithms: AlgorithmMeta[] = (raw.algorithms || []).map((item: any) => ({
    id: item.id,
    name: item.label,
    family: item.family,
    description: item.description,
    complete: item.complete,
    optimal: item.optimality,
    weighted: item.weighted,
    supports_heuristic: item.heuristic_required,
    caveat: optimalityCopy(item.id, raw.defaults?.heuristic),
  }));
  const heuristics: HeuristicMeta[] = (raw.heuristics || []).map((item: any) => ({
    id: item.id,
    name: item.label,
    description: item.description,
    admissible: item.admissible,
    consistent: item.consistent,
    warning: item.warning,
  }));
  return {
    algorithms,
    heuristics,
    scenarios: (raw.scenarios || []).map((item: any) => ({ id: item.id, name: item.label, description: item.description })),
    objectives: [
      { id: "balanced", name: "Balanced cost", description: "Cân bằng bốn thành phần." },
      { id: "distance", name: "Ngắn nhất theo khoảng cách", description: "Ưu tiên distance." },
      { id: "time", name: "Nhanh nhất theo ETA", description: "Ưu tiên travel time và delay." },
      { id: "safety", name: "Rủi ro thấp nhất", description: "Phạt mạnh exposure/risk." },
      { id: "emergency", name: "Emergency response", description: "ETA cao nhất, vẫn tránh incident/risk." },
      { id: "custom", name: "Custom weights", description: "Điều chỉnh trực tiếp bằng sliders." },
    ],
    multi_algorithms: (raw.multi_route_methods || []).map((item: any) => ({
      id: item.id,
      name: item.label,
      description: item.description,
      complete: true,
      optimal: item.exact,
      caveat: item.exact ? "Tối ưu chính xác trong giới hạn số điểm dừng hỗ trợ." : "Xấp xỉ có seed cố định để kết quả lặp lại được.",
    })),
    defaults: {
      algorithm: raw.defaults?.algorithm,
      heuristic: raw.defaults?.heuristic,
      scenario: raw.defaults?.scenario,
      objective: "balanced",
      weights: toUiWeights(raw.defaults?.cost_weights),
    },
    dataset: {
      ...(raw.dataset || {}),
      node_count: raw.graph?.node_count,
      directed_edge_count: raw.graph?.directed_edge_count,
    },
  };
}

function congestionLevel(traffic: any): number {
  const label = String(traffic?.congestion || "").toLowerCase();
  const byLabel = label.includes("severe") || label.includes("gridlock") ? 5
    : label.includes("heavy") || label.includes("high") ? 4
      : label.includes("moderate") || label.includes("medium") ? 3
        : label.includes("light") ? 2 : 1;
  const byMultiplier = 1 + Math.max(0, Number(traffic?.multiplier || 1) - 1) * 3.5;
  return Math.min(5, Math.max(byLabel, byMultiplier));
}

function friendlyLocationName(value: unknown): string {
  const name = String(value || "").trim();
  if (!name || /^osm[_\s-]/i.test(name) || /giao\s+lộ\s+osm\s+\d+/i.test(name)) {
    return "Giao lộ chưa đặt tên";
  }
  return name;
}

function normalizeGraph(raw: any): GraphPayload {
  const box = raw.summary?.bounding_box;
  return {
    name: raw.dataset?.name || "Đà Nẵng emergency graph",
    city: raw.dataset?.city || "Đà Nẵng",
    description: raw.dataset?.description,
    source: raw.dataset?.source,
    generated_at: raw.dataset?.generated_at,
    center: box ? { lat: (box.south + box.north) / 2, lon: (box.west + box.east) / 2 } : undefined,
    bounds: box ? [[box.south, box.west], [box.north, box.east]] : undefined,
    scenario: raw.scenario?.id,
    stats: {
      node_count: raw.summary?.node_count,
      directed_edge_count: raw.summary?.directed_edge_count,
      max_speed_kph: raw.summary?.max_speed_kph,
    },
    nodes: (raw.nodes || []).map((node: any) => ({
      ...node,
      name: friendlyLocationName(node.name),
      short_name: friendlyLocationName(node.short_name || node.name),
      is_hospital: node.kind === "hospital" || Boolean(node.attributes?.emergency_destination),
      district: node.attributes?.district,
      address: node.attributes?.address,
      tags: node.attributes,
    })),
    edges: (raw.directed_edges || []).map((edge: any) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      name: edge.road_name,
      road_type: edge.road_class,
      distance_m: edge.distance_m,
      estimated_time_min: edge.traffic?.travel_time_s == null ? undefined : edge.traffic.travel_time_s / 60,
      travel_time_min: edge.traffic?.travel_time_s == null ? undefined : edge.traffic.travel_time_s / 60,
      congestion: congestionLevel(edge.traffic),
      risk: edge.risk,
      direction: "one_way",
      oneway: true,
      closed: edge.traffic?.closed,
      speed_kph: edge.traffic?.effective_speed_kph ?? edge.speed_kph,
      flags: [
        edge.attributes?.bridge && "cầu",
        edge.attributes?.flood_prone && "nguy cơ ngập (mô phỏng)",
        edge.attributes?.incident_prone && "điểm sự cố (mô phỏng)",
        edge.traffic?.closed && "đang đóng trong scenario",
      ].filter(Boolean),
      geometry: edge.geometry ?? edge.attributes?.geometry,
    })),
  };
}

function geoFeature(raw: any): RouteGeoJson | undefined {
  if (!raw?.coordinates?.length) return undefined;
  return { type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: raw.coordinates } };
}

function normalizeMetrics(raw: any): RouteMetrics {
  return {
    total_distance_m: Number(raw?.distance_m || 0),
    total_time_min: Number(raw?.travel_time_s || 0) / 60,
    total_cost: Number(raw?.path_cost ?? raw?.total_cost ?? 0),
    explored_nodes: Number(raw?.expanded_nodes ?? raw?.pairwise_expanded_nodes ?? 0),
    generated_nodes: Number(raw?.generated_nodes ?? raw?.pairwise_searches ?? 0),
    frontier_peak: Number(raw?.frontier_peak ?? 0),
    processing_time_ms: Number(raw?.runtime_ms || 0),
    hop_count: Number(raw?.hop_count || 0),
    risk_score: Number(raw?.risk_exposure || 0),
  };
}

function normalizeBreakdown(raw: any): CostBreakdown {
  return { ...(raw?.components || {}), total: Number(raw?.total_cost || 0) };
}

const ALGORITHM_LABELS: Record<string, string> = {
  bfs: "Breadth-First Search",
  dfs: "Depth-First Search",
  ucs: "Uniform-Cost Search",
  dijkstra: "Dijkstra",
  astar: "A* Search",
  greedy_best_first: "Greedy Best-First",
  bidirectional: "Bidirectional Search",
  ida_star: "IDA*",
};

const SCENARIO_LABELS: Record<string, string> = {
  normal: "giao thông bình thường",
  morning_rush: "cao điểm buổi sáng",
  evening_rush: "cao điểm buổi chiều",
  heavy_rain: "mưa lớn và ngập cục bộ",
  incident: "sự cố và đóng đường",
  night: "ban đêm",
};

const HEURISTIC_LABELS: Record<string, string> = {
  auto: "tự động",
  zero: "không dùng heuristic",
  haversine: "khoảng cách Haversine",
  euclidean: "khoảng cách Euclidean",
  travel_time: "cận dưới thời gian di chuyển",
  landmark: "cận dưới theo landmark",
};

function heuristicLabel(value?: string): string {
  return HEURISTIC_LABELS[value || ""] || String(value || "đang chọn").replaceAll("_", " ");
}

function optimalityCopy(algorithm: string, heuristic?: string): string {
  if (["ucs", "dijkstra"].includes(algorithm)) return "Bảo đảm tối ưu khi mọi chi phí cạnh đều không âm.";
  if (algorithm === "astar") return `Bảo đảm tối ưu khi heuristic ${heuristicLabel(heuristic)} là admissible và consistent.`;
  if (algorithm === "bfs") return "Tối ưu số chặng, nhưng không nhất thiết tối ưu tổng chi phí có trọng số.";
  if (algorithm === "bidirectional") return "Tối ưu theo điều kiện của chiến lược tìm kiếm hai chiều đang dùng.";
  return "Ưu tiên tốc độ khám phá; không bảo đảm tìm được tuyến có tổng chi phí nhỏ nhất.";
}

function normalizeExplanation(
  raw: any,
  context: { found: boolean; algorithm: string; heuristic?: string; scenario?: string; metrics: RouteMetrics },
) {
  const { found, algorithm, heuristic, scenario, metrics } = context;
  const algorithmName = ALGORITHM_LABELS[algorithm] || "Thuật toán tìm kiếm";
  const scenarioName = SCENARIO_LABELS[scenario || ""] || "kịch bản đang chọn";
  const distance = metrics.total_distance_m >= 1000
    ? `${(metrics.total_distance_m / 1000).toFixed(2)} km`
    : `${Math.round(metrics.total_distance_m)} m`;
  const summary = found
    ? `${algorithmName} đã tìm thấy tuyến ${metrics.hop_count || 0} chặng, dài ${distance}, ETA ${metrics.total_time_min.toFixed(1)} phút trong ${scenarioName}.`
    : `${algorithmName} chưa tìm thấy tuyến khả dụng trong ${scenarioName}.`;
  const reasons = [
    "Điểm số kết hợp khoảng cách, thời gian, độ trễ giao thông và mức rủi ro theo các trọng số đang chọn.",
    `Thuật toán đã mở rộng ${metrics.explored_nodes} nút; frontier lớn nhất có ${metrics.frontier_peak || 0} nút.`,
    heuristic && heuristic !== "zero"
      ? `Heuristic ${heuristicLabel(heuristic)} ước lượng phần chi phí còn lại để ưu tiên hướng khám phá.`
      : undefined,
  ].filter(Boolean) as string[];
  const warnings = raw?.warnings?.length
    ? ["Traffic, sự cố và mức rủi ro trong bản lab là dữ liệu mô phỏng theo kịch bản, không phải dữ liệu điều hành thời gian thực."]
    : [];
  return { summary, reasons, warnings, optimality: optimalityCopy(algorithm, heuristic) };
}

interface PendingTraceFrame {
  current: string;
  parent_id?: string;
  active_edge_id?: string;
  newly_discovered: Set<string>;
  g_score?: number;
  h_score?: number;
  f_score?: number;
  depth?: number;
  phase: "expand" | "finish";
  is_complete?: boolean;
  found?: boolean;
}

/** Convert noisy backend events into one meaningful frame per node expansion. */
function normalizeTrace(raw: any, found: boolean): TraceStep[] {
  const events = raw?.events || [];
  const frames: TraceStep[] = [];
  const visited = new Set<string>();
  const frontier = new Set<string>();
  const parentByNode = new Map<string, string>();
  const edgeByNode = new Map<string, string>();
  const linkByNode = new Map<string, { source: string; target: string; edge_id?: string }>();
  const exploredEdges = new Set<string>();
  const frontierEdges = new Set<string>();
  let pending: PendingTraceFrame | undefined;

  const snapshot = (frame: PendingTraceFrame, reason: string): TraceStep => ({
    step: frames.length,
    current: frame.current,
    phase: frame.phase,
    is_complete: frame.is_complete,
    found: frame.found,
    parent_id: frame.parent_id,
    active_edge_id: frame.active_edge_id,
    active_link: frame.parent_id ? { source: frame.parent_id, target: frame.current, edge_id: frame.active_edge_id } : undefined,
    explored_edge_ids: [...exploredEdges],
    frontier_edge_ids: [...frontierEdges],
    explored_links: [...visited].flatMap((node) => linkByNode.get(node) ? [linkByNode.get(node)!] : []),
    frontier_links: [...frontier].flatMap((node) => linkByNode.get(node) ? [linkByNode.get(node)!] : []),
    frontier: [...frontier],
    visited: [...visited],
    explored: [...visited],
    newly_discovered: [...frame.newly_discovered],
    frontier_size: frontier.size,
    explored_count: visited.size,
    g_score: frame.g_score,
    h_score: frame.h_score,
    f_score: frame.f_score,
    depth: frame.depth,
    reason,
    action: frame.phase,
  });

  const flushPending = () => {
    if (!pending) return;
    const discoveredCount = pending.newly_discovered.size;
    const reason = pending.is_complete
      ? "Đã chạm đích và dựng lại tuyến đường tốt nhất."
      : `Đã mở rộng nút hiện tại và cập nhật ${discoveredCount} hướng đi tiềm năng.`;
    frames.push(snapshot(pending, reason));
    pending = undefined;
  };

  for (const event of events) {
    const kind = String(event.event || "");
    const node = event.node_id ? String(event.node_id) : undefined;
    if (kind === "start" && node) {
      frontier.add(node);
      frames.push({
        step: frames.length,
        current: node,
        phase: "start",
        frontier: [...frontier],
        visited: [],
        explored: [],
        newly_discovered: [node],
        explored_edge_ids: [],
        frontier_edge_ids: [],
        frontier_size: 1,
        explored_count: 0,
        g_score: event.g_cost,
        h_score: event.h_cost,
        f_score: event.f_cost,
        depth: event.depth,
        reason: "Khởi tạo frontier tại điểm xuất phát.",
        action: "start",
      });
      continue;
    }

    if (kind === "iteration") {
      flushPending();
      frames.push({
        step: frames.length,
        current: node || frames.at(-1)?.current || "",
        phase: "iteration",
        frontier: [...frontier],
        visited: [...visited],
        explored: [...visited],
        newly_discovered: [],
        explored_edge_ids: [...exploredEdges],
        frontier_edge_ids: [...frontierEdges],
        frontier_size: frontier.size,
        explored_count: visited.size,
        f_score: event.f_cost,
        reason: "Bắt đầu một vòng lặp với ngưỡng tìm kiếm mới.",
        action: "iteration",
      });
      continue;
    }

    if (kind === "expand" && node) {
      flushPending();
      frontier.delete(node);
      visited.add(node);
      const activeEdge = edgeByNode.get(node);
      if (activeEdge) {
        frontierEdges.delete(activeEdge);
        exploredEdges.add(activeEdge);
      }
      pending = {
        current: node,
        parent_id: parentByNode.get(node),
        active_edge_id: activeEdge,
        newly_discovered: new Set<string>(),
        g_score: event.g_cost,
        h_score: event.h_cost,
        f_score: event.f_cost,
        depth: event.depth,
        phase: "expand",
      };
      continue;
    }

    if (["discover", "relax"].includes(kind) && node) {
      frontier.add(node);
      if (event.parent_id) parentByNode.set(node, String(event.parent_id));
      if (event.parent_id) {
        linkByNode.set(node, {
          source: String(event.parent_id),
          target: node,
          edge_id: event.edge_id ? String(event.edge_id) : undefined,
        });
      }
      if (event.edge_id) {
        const edgeId = String(event.edge_id);
        const previousEdge = edgeByNode.get(node);
        if (previousEdge) frontierEdges.delete(previousEdge);
        edgeByNode.set(node, edgeId);
        frontierEdges.add(edgeId);
      }
      pending?.newly_discovered.add(node);
      continue;
    }

    if (kind === "finish") {
      if (pending) {
        pending.phase = "finish";
        pending.is_complete = true;
        pending.found = found;
        if (node) pending.current = node;
        flushPending();
      } else {
        const current = node || frames.at(-1)?.current || "";
        frames.push({
          step: frames.length,
          current,
          phase: "finish",
          is_complete: true,
          found,
          frontier: [...frontier],
          visited: [...visited],
          explored: [...visited],
          newly_discovered: [],
          explored_edge_ids: [...exploredEdges],
          frontier_edge_ids: [...frontierEdges],
          frontier_size: frontier.size,
          explored_count: visited.size,
          reason: "Hoàn tất tìm kiếm và dựng lại tuyến đường.",
          action: "finish",
        });
      }
    }
  }
  flushPending();
  if (frames.length && !frames.some((frame) => frame.is_complete)) {
    frames[frames.length - 1] = { ...frames[frames.length - 1], phase: "finish", is_complete: true, found };
  }
  return frames;
}

function normalizeSearch(raw: any): SearchResponse {
  const algorithm = raw.algorithm?.id || raw.algorithm;
  const heuristic = raw.heuristic?.id || raw.heuristic;
  const scenario = raw.scenario?.id || raw.scenario;
  const metrics = normalizeMetrics(raw.metrics);
  const found = Boolean(raw.found);
  const alternative = raw.alternative ? {
    label: "Tuyến dự phòng khác biệt",
    path: raw.alternative.path || [],
    metrics: normalizeMetrics({ ...raw.alternative.metrics, ...raw.alternative.cost_breakdown }),
    explanation: "Tuyến này chủ động tránh một đoạn của phương án chính để tạo lựa chọn dự phòng thực sự khác biệt.",
    route_geojson: geoFeature(raw.alternative.route_geojson),
  } : null;
  return {
    request_id: raw.request_id,
    found,
    algorithm,
    heuristic,
    scenario,
    path: raw.path || [],
    route_geojson: geoFeature(raw.route_geojson),
    metrics,
    cost_breakdown: normalizeBreakdown(raw.cost_breakdown),
    trace: normalizeTrace(raw.trace, found),
    explanation: normalizeExplanation(raw.explanation, { found, algorithm, heuristic, scenario, metrics }),
    alternative,
    warnings: raw.explanation?.warnings?.length
      ? ["Dữ liệu traffic và sự cố đang được mô phỏng theo kịch bản lab."]
      : [],
    optimality: optimalityCopy(algorithm, heuristic),
  };
}

function normalizeCompare(raw: any): CompareResponse {
  const results = (raw.runs || []).map(normalizeSearch);
  const agreement = raw.agreement;
  return {
    results,
    winner: raw.best_algorithm,
    insight: agreement
      ? `${agreement.unique_path_count} tuyến khác nhau được tạo ra. ${agreement.same_path ? "Tất cả thuật toán đồng thuận cùng một tuyến." : "Expansion strategy đã dẫn tới các tuyến khác nhau."}`
      : undefined,
  };
}

function normalizeMulti(raw: any): MultiRouteResponse {
  const method = raw.method?.id || raw.method;
  const metrics = normalizeMetrics(raw.metrics);
  const found = raw.status === "found";
  return {
    found,
    method,
    order: raw.stop_order || [],
    segments: [],
    route_geojson: geoFeature(raw.route_geojson),
    metrics,
    explanation: normalizeExplanation(raw.explanation, { found, algorithm: method, scenario: raw.scenario?.id || raw.scenario, metrics }),
    optimality: method === "held_karp"
      ? "Bảo đảm tối ưu cho số điểm dừng nằm trong giới hạn của Held–Karp."
      : "Phương pháp heuristic ưu tiên thời gian chạy; không bảo đảm thứ tự ghé tối ưu toàn cục.",
    original_order: raw.requested_stop_ids || [],
  };
}

export const trafficApi = {
  health: () => request<any>("/health"),
  metadata: async () => normalizeMetadata(await request<any>("/metadata")),
  graph: async (scenario: TrafficScenario) => normalizeGraph(await request<any>(`/graph?scenario=${encodeURIComponent(scenario)}`)),
  search: async (body: SearchRequest) => normalizeSearch(await request<any>("/search", {
    method: "POST",
    body: JSON.stringify({
      start_id: body.start,
      goal_id: body.goal,
      algorithm: body.algorithm,
      heuristic: body.heuristic === "auto" ? "travel_time" : body.heuristic,
      scenario: body.scenario,
      cost_weights: toApiWeights(body.weights),
      include_trace: body.trace ?? true,
      max_trace_events: 2_000,
      max_expansions: 100_000,
      include_alternative: true,
    }),
  })),
  compare: async (body: SearchRequest & { algorithms: string[] }) => normalizeCompare(await request<any>("/compare", {
    method: "POST",
    body: JSON.stringify({
      start_id: body.start,
      goal_id: body.goal,
      algorithms: body.algorithms,
      heuristic: body.heuristic === "auto" ? "travel_time" : body.heuristic,
      scenario: body.scenario,
      cost_weights: toApiWeights(body.weights),
      include_trace: true,
      max_trace_events: 500,
      max_expansions: 100_000,
    }),
  })),
  multiRoute: async (body: {
    start: string;
    stops: string[];
    return_to_start: boolean;
    method: string;
    segment_algorithm: string;
    heuristic: string;
    objective: string;
    scenario: string;
    weights: SearchRequest["weights"];
  }) => normalizeMulti(await request<any>("/multi-route", {
    method: "POST",
    body: JSON.stringify({
      start_id: body.start,
      stop_ids: body.stops,
      return_to_start: body.return_to_start,
      method: body.method,
      scenario: body.scenario,
      cost_weights: toApiWeights(body.weights),
      seed: 42,
      max_iterations: 2_000,
      max_expansions: 100_000,
    }),
  })),
};
