import { afterEach, describe, expect, it } from "vitest";

import { ApiError, client, getTransport, parseErrorEnvelope } from "./client";
import { FetchClient } from "./fetch/client";
import { MockClient } from "./mock/client";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("getGraph via mock transport", () => {
  it("matches the §11 graph response shape and counts", async () => {
    const payload = await new MockClient().getGraph();
    expect(payload).toHaveProperty("graph");
    expect(payload.graph).toHaveProperty("nodes");
    expect(payload.graph).toHaveProperty("edges");
    expect(payload.graph).toHaveProperty("geojson");
    expect(payload.metadata.node_count).toBe(31);
    expect(payload.metadata.edge_count).toBe(70);
    expect(payload.bbox).toHaveLength(4);
  });
});

describe("search + catalog + history + version via mock transport", () => {
  it("search returns the §11 body from the fixture", async () => {
    const payload = await new MockClient().search("bfs", "a", "b");
    expect(payload.run.source).toBe("mock");
    expect(payload.run.algorithm).toBe("bfs");
    expect(payload.result.path.length).toBeGreaterThan(1);
    expect(payload.metrics.hops).toBe(payload.result.path.length - 1);
    expect(payload.route?.geometry.type).toBe("LineString");
  });

  it("listAlgorithms returns the §11 catalog wrapper", async () => {
    const { algorithms } = await new MockClient().listAlgorithms();
    expect(algorithms.map((a) => a.id)).toEqual(["bfs", "dfs", "ucs", "greedy", "astar"]);
    expect(algorithms.find((a) => a.id === "bfs")?.mock).toBe(false);
  });

  it.each([
    ["bfs", 31],
    ["dfs", 30],
    ["ucs", 31],
    ["greedy", 22],
    ["astar", 31],
  ])("search(%s) returns its own per-algorithm fixture with the recorded steps", async (algorithm, steps) => {
    const payload = await new MockClient().search(algorithm, "a", "b", true);
    expect(payload.run.algorithm).toBe(algorithm);
    expect(payload.result.steps).toHaveLength(steps);
    expect(payload.result.steps[0]).toHaveProperty("current_node");
    expect(payload.result.steps[0]).toHaveProperty("frontier");
    expect(payload.result.steps[0]).toHaveProperty("reason");
  });

  it("falls back to the BFS fixture for an unknown algorithm", async () => {
    const payload = await new MockClient().search("dijkstra", "a", "b", false);
    expect(payload.result.steps).toHaveLength(31);
    expect(payload.result.path.length).toBeGreaterThan(1);
  });

  it("getHistory returns the §11 runs wrapper and starts empty", async () => {
    const { runs } = await new MockClient().getHistory();
    expect(runs).toEqual([]);
  });

  it("getVersion returns service + api version", async () => {
    const version = await new MockClient().getVersion();
    expect(version.service).toBeTruthy();
    expect(version.version).toBeTruthy();
  });
});

describe("getGraph via fetch transport", () => {
  const original = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = original;
  });

  it("parses a successful response into the §11 shape", async () => {
    globalThis.fetch = async () => jsonResponse(graphFixtureSmall());
    const result = await new FetchClient().getGraph();
    expect(result.graph.nodes).toHaveLength(2);
    expect(result.metadata.schema_version).toBeDefined();
  });

  it("maps a 503 envelope to an ApiError with the §7 code", async () => {
    globalThis.fetch = async () =>
      jsonResponse(
        { error: { code: "GRAPH_NOT_FOUND", message: "Graph files are missing or failed to load." } },
        503,
      );
    const error = await new FetchClient()
      .getGraph()
      .then(
        () => null,
        (e: unknown) => e as ApiError,
      );
    expect(error).toBeInstanceOf(ApiError);
    expect(error?.code).toBe("GRAPH_NOT_FOUND");
  });

  it("maps a non-JSON HTTP error to a generic HTTP_ERROR", async () => {
    globalThis.fetch = async () =>
      new Response("<html>Server Error</html>", {
        status: 500,
        headers: { "Content-Type": "text/html" },
      });
    const error = await new FetchClient()
      .getGraph()
      .then(
        () => null,
        (e: unknown) => e as ApiError,
      );
    expect(error).toBeInstanceOf(ApiError);
    expect(error?.code).toBe("HTTP_ERROR");
  });

  it("search POSTs a snake_case body and parses the §11 response", async () => {
    const sentinel: { url: string; init: RequestInit | undefined } = { url: "", init: undefined };
    globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      sentinel.url = String(input);
      sentinel.init = init;
      return jsonResponse(searchFixtureSmall());
    };
    const result = await new FetchClient().search("bfs", "a", "c", true);
    expect(sentinel.url).toContain("/search");
    const body = JSON.parse(String(sentinel.init?.body));
    expect(body).toEqual({ algorithm: "bfs", start: "a", goal: "c", enable_logging: true });
    expect(result.run.algorithm).toBe("bfs");
  });

  it("maps a 400 search envelope to an ApiError with the §7 code", async () => {
    globalThis.fetch = async () =>
      jsonResponse({ error: { code: "INVALID_INPUT", message: "Unknown node id." } }, 400);
    const error = await new FetchClient()
      .search("bfs", "x", "y")
      .then(
        () => null,
        (e: unknown) => e as ApiError,
      );
    expect(error).toBeInstanceOf(ApiError);
    expect(error?.code).toBe("INVALID_INPUT");
  });

  it.each([
    ["listAlgorithms", "/algorithms"],
    ["getHistory", "/history"],
  ])("%s fetches %s", async (_method, path) => {
    globalThis.fetch = async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/algorithms"))
        return jsonResponse({ algorithms: [{ id: "bfs", label: "BFS", mock: false }] });
      return jsonResponse({ runs: [] });
    };
    const fetchClient = new FetchClient();
    if (path === "/algorithms") {
      const { algorithms } = await fetchClient.listAlgorithms();
      expect(algorithms.map((a) => a.id)).toEqual(["bfs"]);
    } else {
      const { runs } = await fetchClient.getHistory();
      expect(runs).toEqual([]);
    }
  });

  it("getVersion fetches and parses the §11 body", async () => {
    globalThis.fetch = async () =>
      jsonResponse({ service: "svc", version: "1.0.0", api_version: "1.0" });
    const version = await new FetchClient().getVersion();
    expect(version.service).toBe("svc");
    expect(version.api_version).toBe("1.0");
  });
});

describe("client facade + transport selection", () => {
  it("exposes all six API methods through the facade", () => {
    expect(typeof client.getGraph).toBe("function");
    expect(typeof client.getHealth).toBe("function");
    expect(typeof client.search).toBe("function");
    expect(typeof client.listAlgorithms).toBe("function");
    expect(typeof client.getHistory).toBe("function");
    expect(typeof client.getVersion).toBe("function");
  });

  it("selects a MockClient when VITE_API_MODE is not http", () => {
    expect(getTransport()).toBeInstanceOf(MockClient);
  });
});

describe("parseErrorEnvelope", () => {
  it("parses a well-formed §7 envelope", () => {
    const envelope = parseErrorEnvelope({ error: { code: "X", message: "msg", details: { a: 1 } } });
    expect(envelope).toEqual({ error: { code: "X", message: "msg", details: { a: 1 } } });
  });

  it("returns null for malformed input", () => {
    expect(parseErrorEnvelope({})).toBeNull();
    expect(parseErrorEnvelope(null)).toBeNull();
    expect(parseErrorEnvelope({ error: {} })).toBeNull();
  });
});

function graphFixtureSmall(): unknown {
  return {
    graph: {
      nodes: [
        { id: "n1", name: "A", latitude: 1, longitude: 2, kind: "delivery_market", attributes: {} },
        { id: "n2", name: "B", latitude: 3, longitude: 4, kind: "delivery_market", attributes: {} },
      ],
      edges: [],
      geojson: { type: "FeatureCollection", features: [] },
    },
    bbox: [1, 2, 3, 4],
    metadata: { schema_version: "1.0", node_count: 2, edge_count: 0 },
  };
}

function searchFixtureSmall(): unknown {
  return {
    run: { id: "r-1", algorithm: "bfs", source: "mock" },
    result: {
      path: ["a", "b", "c"],
      visited_nodes: ["a", "b", "c"],
      steps: [
        { current_node: "a", frontier: ["b"], reason: "expand" },
        { current_node: "b", frontier: ["c"], reason: "expand" },
      ],
      total_distance_km: 1.5,
      total_time_min: 2,
      total_cost: 3,
      processing_time_ms: 1,
      explanation: "ok",
    },
    metrics: { hops: 2, nodes_visited: 3, distance_km: 1.5, time_min: 2, cost: 3, processing_time_ms: 1 },
    route: {
      type: "Feature",
      geometry: { type: "LineString", coordinates: [[1, 2], [3, 4]] },
    },
  };
}
