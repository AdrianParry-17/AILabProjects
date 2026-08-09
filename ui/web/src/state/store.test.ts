import { afterEach, describe, expect, it, vi } from "vitest";

import { useStore } from "./store";
import { client } from "../api/client";
import type { SearchResult } from "../api/types";

describe("graph slice + loadGraph", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("populates graph from the mock transport and reaches Ready", async () => {
    const spy = vi.spyOn(client, "getGraph");
    // real call uses the mock fixture (VITE_API_MODE defaults to mock)
    await useStore.getState().loadGraph();
    const state = useStore.getState();
    expect(state.status).toBe("Ready");
    expect(state.graph?.edges).toHaveLength(70);
    expect(state.graph?.nodes).toHaveLength(31);
    expect(state.graph?.bbox).toHaveLength(4);
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it("reaches Error when the graph fails to load", async () => {
    vi.spyOn(client, "getGraph").mockRejectedValue(new Error("boom"));
    await useStore.getState().loadGraph();
    const state = useStore.getState();
    expect(state.status).toBe("Error");
    expect(state.error).toContain("boom");
  });
});

describe("catalog slice + loadCatalog", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    useStore.setState({ catalog: [] });
  });

  it("populates the catalog from the transport", async () => {
    const spy = vi.spyOn(client, "listAlgorithms").mockResolvedValue({
      algorithms: [
        { id: "bfs", label: "Breadth-First Search", mock: false },
        { id: "greedy", label: "Greedy Best-First Search", mock: true },
      ],
    } as never);
    await useStore.getState().loadCatalog();
    const ids = useStore.getState().catalog.map((a) => a.id);
    expect(ids).toEqual(["bfs", "greedy"]);
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it("clears the catalog when the fetch fails", async () => {
    vi.spyOn(client, "listAlgorithms").mockRejectedValue(new Error("boom"));
    await useStore.getState().loadCatalog();
    expect(useStore.getState().catalog).toEqual([]);
  });
});

describe("search slice + runSearch", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    useStore.setState({
      selectedAlgorithm: null,
      start: null,
      goal: null,
      result: null,
      busy: false,
    });
  });

  const RESULT: SearchResult = {
    path: ["a", "b"],
    visited_nodes: ["a", "b"],
    steps: [{ current_node: "a", frontier: ["b"], reason: "expand" }],
    total_distance_km: 1,
    total_time_min: 1,
    total_cost: 1,
    processing_time_ms: 1,
    explanation: "ok",
  };

  it("runSearch keeps animation logging enabled (true)", async () => {
    const spy = vi.spyOn(client, "search").mockResolvedValue({
      run: { id: "r-1", algorithm: "bfs", source: "real" },
      result: RESULT,
      metrics: { hops: 1, nodes_visited: 2, distance_km: 1, time_min: 1, cost: 1, processing_time_ms: 1 },
      route: null,
    } as never);
    useStore.setState({
      selectedAlgorithm: "bfs",
      start: "a",
      goal: "b",
      status: "Idle",
      result: null,
    });
    await useStore.getState().runSearch();
    expect(spy).toHaveBeenCalledWith("bfs", "a", "b", true);
    expect(useStore.getState().result?.path).toEqual(["a", "b"]);
  });
});

describe("renderer slice + setRenderer (T08)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    useStore.setState({ renderer: "map" });
  });

  it("defaults to the map renderer per MAP_RENDERING_SPEC §2", () => {
    expect(useStore.getState().renderer).toBe("map");
  });

  it("flips between graph and map without touching the backend transport", () => {
    const graphSpy = vi.spyOn(client, "getGraph");
    const searchSpy = vi.spyOn(client, "search");
    const historySpy = vi.spyOn(client, "getHistory");
    const catalogSpy = vi.spyOn(client, "listAlgorithms");

    useStore.getState().setRenderer("graph");
    expect(useStore.getState().renderer).toBe("graph");
    useStore.getState().setRenderer("map");
    expect(useStore.getState().renderer).toBe("map");

    expect(graphSpy).not.toHaveBeenCalled();
    expect(searchSpy).not.toHaveBeenCalled();
    expect(historySpy).not.toHaveBeenCalled();
    expect(catalogSpy).not.toHaveBeenCalled();
  });

  it("does not reset search/playback/selection when the renderer changes", () => {
    useStore.setState({
      result: { path: ["a", "b"], visited_nodes: ["a", "b"], steps: [{ current_node: "a", frontier: ["b"], reason: "expand" }], total_distance_km: 1, total_time_min: 1, total_cost: 1, processing_time_ms: 1, explanation: "ok" },
      activeIndex: 0,
      playing: true,
      selectedNode: "a",
      selectedAlgorithm: "bfs",
      start: "a",
      goal: "b",
    });

    const before = {
      activeIndex: useStore.getState().activeIndex,
      playing: useStore.getState().playing,
      result: useStore.getState().result,
      selectedNode: useStore.getState().selectedNode,
    };

    useStore.getState().setRenderer("map");
    useStore.getState().setRenderer("graph");

    const after = useStore.getState();
    expect(after.activeIndex).toBe(before.activeIndex);
    expect(after.playing).toBe(before.playing);
    expect(after.result).toEqual(before.result);
    expect(after.selectedNode).toBe(before.selectedNode);
  });
});

describe("history slice + replayRun", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    useStore.setState({
      history: [],
      historyLoading: false,
      replay: false,
      replayRunId: null,
      result: null,
      status: "Idle",
    });
  });

  const RESULT: SearchResult = {
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
  };

  function seedRun() {
    useStore.setState({
      history: [
        {
          id: "r-1",
          algorithm: "bfs",
          start: "a",
          goal: "c",
          source: "real",
          created_at: "2024-01-01T00:00:00Z",
          hops: 2,
          result: RESULT,
        },
      ],
    });
  }

  it("replayRun hydrates result + animation from stored steps without a network call", () => {
    seedRun();
    const searchSpy = vi.spyOn(client, "search");
    useStore.getState().replayRun("r-1");
    const state = useStore.getState();
    expect(state.result?.path).toEqual(["a", "b", "c"]);
    expect(state.status).toBe("Replay");
    expect(state.replay).toBe(true);
    expect(state.replayRunId).toBe("r-1");
    expect(state.activeIndex).toBe(0);
    expect(searchSpy).not.toHaveBeenCalled();
  });

  it("replayRun ignores unknown run ids", () => {
    seedRun();
    useStore.getState().replayRun("r-404");
    const state = useStore.getState();
    expect(state.status).toBe("Idle");
    expect(state.result).toBeNull();
  });

  it("loadHistory toggles historyLoading and persists runs", async () => {
    const spy = vi.spyOn(client, "getHistory").mockResolvedValue({
      runs: [
        {
          id: "r-9",
          algorithm: "ucs",
          start: "a",
          goal: "z",
          source: "mock",
          created_at: "2024-01-01T00:00:00Z",
          hops: 5,
        },
      ],
    });
    const promise = useStore.getState().loadHistory();
    expect(useStore.getState().historyLoading).toBe(true);
    await promise;
    const state = useStore.getState();
    expect(state.historyLoading).toBe(false);
    expect(state.history.map((r) => r.id)).toEqual(["r-9"]);
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it("loadHistory clears the loading flag when the fetch fails", async () => {
    vi.spyOn(client, "getHistory").mockRejectedValue(new Error("boom"));
    await useStore.getState().loadHistory();
    expect(useStore.getState().historyLoading).toBe(false);
  });
});

describe("backend info slice + loadBackendInfo (T14)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    useStore.setState({ backendOk: null, version: null });
  });

  it("populates backendOk and version from the existing /health + /version transports", async () => {
    vi.spyOn(client, "getHealth").mockResolvedValue({ status: "ok" } as never);
    vi.spyOn(client, "getVersion").mockResolvedValue({
      service: "hcmc-delivery",
      version: "0.1.0",
      api_version: "1.2.3",
    } as never);
    await useStore.getState().loadBackendInfo();
    const state = useStore.getState();
    expect(state.backendOk).toBe(true);
    expect(state.version).toBe("1.2.3");
  });

  it("marks backendOk=false when the health probe rejects (no UI crash)", async () => {
    vi.spyOn(client, "getHealth").mockRejectedValue(new Error("network"));
    vi.spyOn(client, "getVersion").mockResolvedValue({
      service: "hcmc-delivery",
      version: "0.1.0",
      api_version: "9.9.9",
    } as never);
    await useStore.getState().loadBackendInfo();
    const state = useStore.getState();
    expect(state.backendOk).toBe(false);
    expect(state.version).toBe("9.9.9");
  });

  it("treats non-ok health payloads as backend down without overwriting a known version", async () => {
    useStore.setState({ version: "0.0.5" });
    vi.spyOn(client, "getHealth").mockResolvedValue({ status: "degraded" } as never);
    vi.spyOn(client, "getVersion").mockRejectedValue(new Error("nope"));
    await useStore.getState().loadBackendInfo();
    const state = useStore.getState();
    expect(state.backendOk).toBe(false);
    expect(state.version).toBe("0.0.5");
  });
});