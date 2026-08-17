import { afterEach, describe, expect, it, vi } from "vitest";
import { trafficApi } from "./api";

function jsonResponse(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("FastAPI contract adapter", () => {
  it("normalizes backend registries into UI metadata", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({
      dataset: { id: "hcmc", name: "HCMC delivery graph", city: "Thành phố Hồ Chí Minh" },
      graph: { node_count: 1103, directed_edge_count: 2279 },
      algorithms: [{ id: "astar", label: "A* Search", family: "Informed", weighted: true, heuristic_required: true, complete: true, optimality: "optimal with admissible h", description: "g+h" }],
      heuristics: [{ id: "haversine", label: "Haversine", description: "lower bound", admissible: true, consistent: true }],
      scenarios: [{ id: "heavy_rain", label: "Mưa lớn", description: "synthetic rain" }],
      multi_route_methods: [{ id: "held_karp", label: "Held–Karp", exact: true, description: "exact", max_recommended_stops: 10 }],
      defaults: { algorithm: "astar", heuristic: "haversine", scenario: "heavy_rain", cost_weights: { distance: .25, travel_time: .5, traffic_delay: .2, risk: .05 } },
    })));

    const metadata = await trafficApi.metadata();
    expect(metadata.algorithms[0]).toMatchObject({ id: "astar", name: "A* Search", supports_heuristic: true });
    expect(metadata.heuristics[0]).toMatchObject({ admissible: true, consistent: true });
    expect(metadata.multi_algorithms?.[0]).toMatchObject({ id: "held_karp", optimal: true });
    expect(metadata.defaults?.weights).toEqual({ distance: .25, time: .5, congestion: .2, risk: .05 });
  });

  it("preserves real OSM edge geometry and scenario traffic", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({
      dataset: { name: "OSM graph", city: "Thành phố Hồ Chí Minh", source: "OpenStreetMap" },
      summary: { node_count: 2, directed_edge_count: 1, max_speed_kph: 50, bounding_box: { south: 10.76, west: 106.68, north: 10.79, east: 106.71 } },
      scenario: { id: "incident" },
      nodes: [
        { id: "a", name: "A", kind: "intersection", lat: 10.77, lon: 106.69, attributes: {} },
        { id: "b", name: "Chợ Bến Thành", kind: "delivery_market", lat: 10.78, lon: 106.70, attributes: { delivery_destination: true, routing_component: "primary" } },
      ],
      directed_edges: [{
        id: "ab", source: "a", target: "b", distance_m: 1200, speed_kph: 40,
        road_name: "Đường A", road_class: "primary", risk: .2, traversable: true, direction: "two-way",
        attributes: { bridge: true }, geometry: [[106.69, 10.77], [106.695, 10.775], [106.70, 10.78]],
        traffic: { multiplier: 1.8, travel_time_s: 180, effective_speed_kph: 24, congestion: "heavy", closed: false },
      }],
    })));

    const graph = await trafficApi.graph("incident");
    expect(graph.nodes[1]).toMatchObject({ is_delivery_point: true, poi_category: "market", routing_component: "primary" });
    expect(graph.edges[0].geometry).toHaveLength(3);
    expect(graph.edges[0]).toMatchObject({ name: "Đường A", road_type: "primary", travel_time_min: 3, closed: false, oneway: false, traversable: true });
    expect(graph.edges[0].congestion).toBeGreaterThanOrEqual(4);
  });

  it("maps UI search fields to strict backend names and rebuilds visual trace sets", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      request_id: "r1", status: "found", found: true,
      algorithm: { id: "astar" }, heuristic: { id: "travel_time" }, scenario: { id: "morning_rush" },
      path: ["a", "b"], edge_ids: ["ab"],
      route_geojson: { type: "LineString", coordinates: [[108, 16], [108.01, 16.01]] },
      metrics: { runtime_ms: .4, expanded_nodes: 2, generated_nodes: 2, frontier_peak: 1, hop_count: 1, path_cost: 1.25, distance_m: 1200, travel_time_s: 180, risk_exposure: .2 },
      trace: { events: [
        { step: 0, event: "start", node_id: "a", message: "seed" },
        { step: 1, event: "expand", node_id: "a", message: "pop a" },
        { step: 2, event: "discover", node_id: "b", parent_id: "a", edge_id: "ab", message: "push b", g_cost: 1.25 },
        { step: 3, event: "expand", node_id: "b", message: "goal" },
      ] },
      explanation: { summary: "Fast route", optimality: "guaranteed", traffic_note: "rush", cost_model: "weighted", heuristic_note: "admissible", warnings: [] },
      cost_breakdown: { components: { distance: .25, travel_time: 1 }, total_cost: 1.25 },
      alternative: {
        algorithm: "dijkstra",
        reason: "Best route found while excluding primary edge osm_path_99.",
        path: ["a", "b"],
        route_geojson: { type: "LineString", coordinates: [[108, 16], [108.02, 16.02]] },
        metrics: { path_cost: 1.5, hop_count: 1, runtime_ms: .5 },
        cost_breakdown: { distance_m: 1300, travel_time_s: 210, total_cost: 1.5 },
      },
    }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await trafficApi.search({
      start: "a", goal: "b", algorithm: "astar", heuristic: "travel_time",
      objective: "priority_delivery", scenario: "morning_rush",
      weights: { distance: 1, time: 4, congestion: 2, risk: 1 }, trace: true,
    });

    const request = JSON.parse(String((fetchMock.mock.calls[0][1] as RequestInit).body));
    expect(request).toMatchObject({
      start_id: "a", goal_id: "b", algorithm: "astar", scenario: "morning_rush",
      cost_weights: { distance: 1, travel_time: 4, traffic_delay: 2, risk: 1 },
    });
    expect(request).not.toHaveProperty("objective");
    expect(result.route_geojson?.geometry.coordinates).toHaveLength(2);
    expect(result.trace.at(-1)?.visited).toEqual(["a", "b"]);
    expect(result.trace).toHaveLength(3);
    expect(result.trace[1]).toMatchObject({ phase: "expand", current: "a", newly_discovered: ["b"] });
    expect(result.trace[1].frontier).toContain("b");
    expect(result.trace[1].frontier_edge_ids).toContain("ab");
    expect(result.trace.at(-1)?.explored_edge_ids).toContain("ab");
    expect(result.trace.map((step) => step.reason).join(" ")).not.toMatch(/pop a|push b/);
    expect(result.metrics.total_time_min).toBe(3);
    expect(result.alternative?.metrics).toMatchObject({ total_distance_m: 1300, total_time_min: 3.5, total_cost: 1.5 });
    expect(`${result.alternative?.label} ${result.alternative?.explanation}`).not.toMatch(/osm_path_|excluding primary edge/i);
  });

  it("keeps multi-stop leg routes and per-leg costs", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({
      status: "found",
      method: { id: "two_opt" },
      scenario: { id: "normal" },
      requested_stop_ids: ["market"],
      stop_order: ["market"],
      route_geojson: { type: "LineString", coordinates: [[106.69, 10.77], [106.70, 10.78]] },
      metrics: { runtime_ms: 2, pairwise_expanded_nodes: 8, pairwise_searches: 2, hop_count: 1, path_cost: 1.2, distance_m: 900, travel_time_s: 180 },
      segments: [{
        from_id: "hub", to_id: "market", path: ["hub", "market"], edge_ids: ["hm"],
        route_geojson: { type: "LineString", coordinates: [[106.69, 10.77], [106.70, 10.78]] },
        cost_breakdown: { distance_m: 900, travel_time_s: 180, components: { distance: .3, travel_time: .9 }, total_cost: 1.2 },
      }],
      explanation: { warnings: [] },
    })));

    const result = await trafficApi.multiRoute({
      start: "hub", stops: ["market"], return_to_start: false, method: "two_opt",
      segment_algorithm: "dijkstra", heuristic: "zero", objective: "balanced", scenario: "normal",
      weights: { distance: 1, time: 1, congestion: 1, risk: 1 },
    });

    expect(result.segments).toHaveLength(1);
    expect(result.segments[0]).toMatchObject({ from_id: "hub", to_id: "market", distance_m: 900, travel_time_min: 3, total_cost: 1.2 });
    expect(result.explanation).toMatchObject({ optimality: expect.stringContaining("heuristic") });
    expect(typeof result.explanation === "object" ? result.explanation.reasons?.join(" ") : "").toContain("Dijkstra");
  });

  it("labels a truncated trace as a summary jump and preserves bidirectional optimality", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({
      request_id: "r-truncated", status: "found", found: true,
      algorithm: { id: "bidirectional_dijkstra" }, heuristic: { id: "zero" }, scenario: { id: "normal" },
      path: ["a", "b"], edge_ids: ["ab"],
      route_geojson: { type: "LineString", coordinates: [[106.69, 10.77], [106.70, 10.78]] },
      metrics: { runtime_ms: 1, expanded_nodes: 2, generated_nodes: 2, frontier_peak: 1, hop_count: 1, path_cost: 1, distance_m: 100, travel_time_s: 20 },
      trace: {
        truncated: true,
        events: [
          { step: 0, event: "start", node_id: "a" },
          { step: 1, event: "expand", node_id: "a" },
          { step: 2, event: "discover", node_id: "b", parent_id: "a", edge_id: "ab" },
        ],
      },
      explanation: { warnings: [] },
      cost_breakdown: { components: { distance: 1 }, total_cost: 1 },
    })));

    const result = await trafficApi.search({
      start: "a", goal: "b", algorithm: "bidirectional_dijkstra", heuristic: "zero",
      objective: "balanced", scenario: "normal",
      weights: { distance: 1, time: 1, congestion: 1, risk: 1 }, trace: true,
    });

    expect(result.trace.at(-1)).toMatchObject({ phase: "finish", is_complete: true, trace_truncated: true });
    expect(result.trace.at(-2)?.is_complete).not.toBe(true);
    expect(result.trace.at(-1)?.reason).toContain("đạt giới hạn");
    expect(result.optimality).toContain("chi phí cạnh đều không âm");
  });

  it("surfaces FastAPI structured validation errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({
      error: { code: "validation_error", message: "Request validation failed", details: [{ loc: ["body", "start_id"] }] },
    }, 422)));
    await expect(trafficApi.health()).rejects.toMatchObject({ status: 422, message: "Request validation failed" });
  });
});
