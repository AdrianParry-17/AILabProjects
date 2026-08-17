import type {
  AlgorithmMeta,
  CostBreakdown,
  CostWeights,
  GraphPayload,
  HeuristicMeta,
  MetadataPayload,
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
      { id: "priority_delivery", name: "Giao ưu tiên", description: "Ưu tiên ETA và độ trễ cho đơn cần giao sớm." },
      { id: "custom", name: "Custom weights", description: "Điều chỉnh trực tiếp bằng sliders." },
    ],
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

export interface TrafficOverlay {
  scenario: string;
  edges: Array<{
    edge_id: string;
    multiplier: number;
    effective_speed_kph: number;
    travel_time_s?: number;
    congestion: string;
    level: number;
    closed: boolean;
  }>;
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
    name: raw.dataset?.name || "HCMC delivery graph",
    city: raw.dataset?.city || "Thành phố Hồ Chí Minh",
    description: raw.dataset?.description,
    source: raw.dataset?.source,
    generated_at: raw.dataset?.generated_at,
    center: box ? { lat: (box.south + box.north) / 2, lon: (box.west + box.east) / 2 } : undefined,
    bounds: box ? [[box.south, box.west], [box.north, box.east]] : undefined,
    scenario: raw.scenario?.id,
    stats: {
      ...(raw.dataset?.stats || {}),
      node_count: raw.summary?.node_count,
      directed_edge_count: raw.summary?.directed_edge_count,
      max_speed_kph: raw.summary?.max_speed_kph,
    },
    nodes: (raw.nodes || []).map((node: any) => ({
      ...node,
      name: friendlyLocationName(node.name),
      short_name: friendlyLocationName(node.short_name || node.name),
      is_delivery_point: node.kind?.startsWith("delivery_") || Boolean(node.attributes?.delivery_destination),
      poi_category: node.attributes?.delivery_category || String(node.kind || "").replace(/^delivery_/, ""),
      routing_component: node.attributes?.routing_component,
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
      direction: String(edge.direction || edge.attributes?.source_direction || "directed").replace("-", "_"),
      oneway: !["two-way", "two_way"].includes(String(edge.direction || edge.attributes?.source_direction)),
      closed: edge.traffic?.closed,
      traversable: edge.traversable !== false,
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
  bidirectional_dijkstra: "Bidirectional Dijkstra",
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
  if (["ucs", "dijkstra", "bidirectional_dijkstra"].includes(algorithm)) return "Bảo đảm tối ưu khi mọi chi phí cạnh đều không âm.";
  if (["astar", "ida_star"].includes(algorithm)) return `Bảo đảm tối ưu khi heuristic ${heuristicLabel(heuristic)} là admissible và consistent.`;
  if (algorithm === "bfs") return "Tối ưu số chặng, nhưng không nhất thiết tối ưu tổng chi phí có trọng số.";
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
  const visualNodeLimit = 260;
  const visualEdgeLimit = 300;
  const events = raw?.events || [];
  const frames: TraceStep[] = [];
  const visited = new Set<string>();
  const visitedOrder: string[] = [];
  const frontier = new Set<string>();
  const parentByNode = new Map<string, string>();
  const edgeByNode = new Map<string, string>();
  const exploredEdges = new Set<string>();
  const exploredEdgeOrder: string[] = [];
  const frontierEdges = new Set<string>();
  let pending: PendingTraceFrame | undefined;
  const setTail = <T,>(values: Set<T>, limit: number): T[] => [...values].slice(-limit);
  const arrayTail = <T,>(values: T[], limit: number): T[] => values.slice(-limit);

  const snapshot = (frame: PendingTraceFrame, reason: string): TraceStep => ({
    step: frames.length,
    current: frame.current,
    phase: frame.phase,
    is_complete: frame.is_complete,
    found: frame.found,
    parent_id: frame.parent_id,
    active_edge_id: frame.active_edge_id,
    active_link: frame.parent_id ? { source: frame.parent_id, target: frame.current, edge_id: frame.active_edge_id } : undefined,
    explored_edge_ids: arrayTail(exploredEdgeOrder, visualEdgeLimit),
    frontier_edge_ids: setTail(frontierEdges, visualEdgeLimit),
    frontier: setTail(frontier, visualNodeLimit),
    visited: arrayTail(visitedOrder, visualNodeLimit),
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
        frontier: setTail(frontier, visualNodeLimit),
        visited: arrayTail(visitedOrder, visualNodeLimit),
        newly_discovered: [],
        explored_edge_ids: arrayTail(exploredEdgeOrder, visualEdgeLimit),
        frontier_edge_ids: setTail(frontierEdges, visualEdgeLimit),
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
      if (!visited.has(node)) {
        visited.add(node);
        visitedOrder.push(node);
      }
      const activeEdge = edgeByNode.get(node);
      if (activeEdge) {
        frontierEdges.delete(activeEdge);
        if (!exploredEdges.has(activeEdge)) {
          exploredEdges.add(activeEdge);
          exploredEdgeOrder.push(activeEdge);
        }
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
          frontier: setTail(frontier, visualNodeLimit),
          visited: arrayTail(visitedOrder, visualNodeLimit),
          newly_discovered: [],
          explored_edge_ids: arrayTail(exploredEdgeOrder, visualEdgeLimit),
          frontier_edge_ids: setTail(frontierEdges, visualEdgeLimit),
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
    const last = frames[frames.length - 1];
    const completion: TraceStep = {
      ...last,
      step: raw?.truncated ? frames.length : last.step,
      phase: "finish",
      is_complete: true,
      found,
      trace_truncated: Boolean(raw?.truncated),
      newly_discovered: [],
      reason: raw?.truncated
        ? "Nhật ký trực quan đã đạt giới hạn; chuyển tới kết quả cuối do search engine trả về."
        : "Hoàn tất tìm kiếm và dựng lại tuyến đường.",
      action: "finish",
    };
    if (raw?.truncated) frames.push(completion);
    else frames[frames.length - 1] = completion;
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

export const trafficApi = {
  health: () => request<any>("/health"),
  metadata: async () => normalizeMetadata(await request<any>("/metadata")),
  graph: async (scenario: TrafficScenario) => normalizeGraph(await request<any>(`/graph?scenario=${encodeURIComponent(scenario)}&include_geojson=false&compact=true`)),
  traffic: async (scenario: TrafficScenario): Promise<TrafficOverlay> => {
    const raw = await request<any>(`/traffic?scenario=${encodeURIComponent(scenario)}`);
    return {
      scenario: String(raw.scenario?.id || scenario),
      edges: (raw.edges || []).map((status: any) => ({
        edge_id: String(status.edge_id),
        multiplier: Number(status.multiplier || 1),
        effective_speed_kph: Number(status.effective_speed_kph || 0),
        travel_time_s: status.travel_time_s == null ? undefined : Number(status.travel_time_s),
        congestion: String(status.congestion || "light"),
        level: congestionLevel(status),
        closed: Boolean(status.closed),
      })),
    };
  },
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
      max_trace_events: 1_200,
      max_expansions: 100_000,
      include_alternative: true,
    }),
  })),
};
