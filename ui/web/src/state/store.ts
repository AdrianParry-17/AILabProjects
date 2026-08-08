import { create } from "zustand";

import { client } from "../api/client";
import { isEmpty } from "../services/animation";
import type {
  AlgorithmSummary,
  DeliveryEdge,
  DeliveryNode,
  HistoryRun,
  SearchResult,
} from "../api/types";

/** GUI_ROADMAP §8 — the only valid statuses. */
export type Status =
  | "Idle"
  | "Loading"
  | "Ready"
  | "Playing"
  | "Paused"
  | "Finished"
  | "Error"
  | "Replay";

/** `search` slice (COMPONENT_SPEC §0.2): selection + the resulting run. */
export interface SearchState {
  selectedAlgorithm: string | null;
  start: string | null;
  goal: string | null;
  result: SearchResult | null;
  source: "real" | "mock" | null;
  busy: boolean;
  searchError: string | null;
  setAlgorithm: (id: string | null) => void;
  setStart: (id: string | null) => void;
  setGoal: (id: string | null) => void;
  setStatus: (s: Status) => void;
  runSearch: () => Promise<void>;
}

/** `animation` slice (§0.2): playback cursor + cadence. */
export interface AnimationSlice {
  activeIndex: number;
  playing: boolean;
  speed: number;
  advanceStep: () => void;
  stepTo: (i: number) => void;
  play: () => void;
  pause: () => void;
  restart: () => void;
  setSpeed: (m: number) => void;
}

/** Graph slice (§0.2): the loaded delivery graph + selection + load action. */
export interface GraphState extends SearchState, AnimationSlice {
  graph: {
    nodes: DeliveryNode[];
    edges: DeliveryEdge[];
    bbox: [number, number, number, number];
  } | null;
  status: Status;
  error: string | null;
  selectedNode: string | null;
  hoveredNode: string | null;
  loadGraph: () => Promise<void>;
  selectNode: (id: string | null) => void;
  setHoveredNode: (id: string | null) => void;

  /** Renderer slice (T08): active visualization renderer. Switching is a pure
   *  frontend state change — `setRenderer` does not call any backend transport. */
  renderer: "graph" | "map";
  setRenderer: (r: "graph" | "map") => void;

  /** Catalog slice: the algorithm catalog fetched once, centrally. */
  catalog: AlgorithmSummary[];
  loadCatalog: () => Promise<void>;

  /** History slice (§0.2): recorded runs + replay. */
  history: RecordedRun[];
  historyLoading: boolean;
  replay: boolean;
  replayRunId: string | null;
  loadHistory: () => Promise<void>;
  replayRun: (id: string) => void;
}

/** A stored run: the §11 summary plus the full `result` needed for replay. */
export interface RecordedRun extends HistoryRun {
  result: SearchResult | null;
}

export const useStore = create<GraphState>()((set, get) => ({
  graph: null,
  status: "Idle",
  error: null,
  selectedNode: null,
  hoveredNode: null,
  catalog: [],
  history: [],
  historyLoading: false,
  replay: false,
  replayRunId: null,
  /** Active visualization renderer (UI_IMPLEMENTATION_PLAN §7 T08,
   *  MAP_RENDERING_SPEC §2). Default is "map" per spec; in P2 the map branch
   *  mounts the same GraphCanvas host until Leaflet lands in P3 (T11). */
  renderer: "map",
  setRenderer: (r) => set({ renderer: r }),

  loadCatalog: async () => {
    try {
      const payload = await client.listAlgorithms();
      set({ catalog: payload.algorithms });
    } catch {
      set({ catalog: [] });
    }
  },

  loadGraph: async () => {
    set({ status: "Loading", error: null });
    try {
      const payload = await client.getGraph();
      set({
        graph: {
          nodes: payload.graph.nodes,
          edges: payload.graph.edges,
          bbox: payload.bbox,
        },
        status: "Ready",
        error: null,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load graph.";
      set({ status: "Error", error: message });
    }
  },

  selectNode: (id) => set({ selectedNode: id }),
  setHoveredNode: (id) => set({ hoveredNode: id }),

  selectedAlgorithm: null,
  start: null,
  goal: null,
  result: null,
  source: null,
  busy: false,
  searchError: null,

  setAlgorithm: (id) => set({ selectedAlgorithm: id }),
  setStart: (id) => set({ start: id }),
  setGoal: (id) => set({ goal: id }),
  setStatus: (s) => set({ status: s }),

  runSearch: async () => {
    const { start, goal, selectedAlgorithm } = get();
    if (!start || !goal || !selectedAlgorithm || start === goal) {
      set({ searchError: "Choose different start and destination points.", busy: false, status: "Error" });
      return;
    }
    set({ busy: true, status: "Loading", searchError: null });
    try {
      // Logging stays ON so the animation + replay always have SearchSteps.
      const response = await client.search(selectedAlgorithm, start, goal, true);
      const steps = response.result.steps ?? [];
      const run: RecordedRun = {
        id: response.run.id,
        algorithm: response.run.algorithm,
        start,
        goal,
        source: response.run.source,
        created_at: new Date().toISOString(),
        hops: response.metrics.hops,
        result: response.result,
      };
      set({
        busy: false,
        result: response.result,
        source: response.run.source === "mock" ? "mock" : "real",
        activeIndex: isEmpty(steps) ? -1 : 0,
        playing: false,
        status: "Ready",
        searchError: null,
        replay: false,
        replayRunId: null,
        history: [run, ...get().history.filter((r) => r.id !== run.id)],
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Search failed.";
      set({ busy: false, status: "Error", searchError: message });
    }
  },

  activeIndex: -1,
  playing: false,
  speed: 1,

  loadHistory: async () => {
    set({ historyLoading: true });
    try {
      const res = await client.getHistory();
      const byId = new Map(get().history.map((r) => [r.id, r]));
      const merged = res.runs.map((summary) => byId.get(summary.id) ?? { ...summary, result: null });
      set({ history: merged, historyLoading: false });
    } catch {
      set({ historyLoading: false });
    }
  },

  replayRun: (id) => {
    const run = get().history.find((r) => r.id === id);
    if (!run || !run.result) return;
    const steps = run.result.steps ?? [];
    set({
      result: run.result,
      source: run.source === "mock" ? "mock" : "real",
      selectedAlgorithm: run.algorithm,
      start: run.start,
      goal: run.goal,
      activeIndex: isEmpty(steps) ? -1 : 0,
      playing: false,
      status: "Replay",
      replay: true,
      replayRunId: id,
      searchError: null,
    });
  },

  advanceStep: () => {
    const s = get();
    const steps = s.result?.steps ?? [];
    if (isEmpty(steps)) return;
    const last = steps.length - 1;
    if (s.activeIndex >= last) {
      set({ status: "Finished", playing: false });
      return;
    }
    const next = s.activeIndex + 1;
    set({
      activeIndex: next,
      status: next === last ? "Finished" : s.status,
      playing: next === last ? false : s.playing,
    });
  },

  stepTo: (i) => {
    const s = get();
    const steps = s.result?.steps ?? [];
    if (isEmpty(steps)) return;
    if (
      s.status !== "Ready" &&
      s.status !== "Paused" &&
      s.status !== "Finished" &&
      s.status !== "Replay"
    ) {
      return;
    }
    const last = steps.length - 1;
    const clamped = Math.max(0, Math.min(i, last));
    set({
      activeIndex: clamped,
      playing: false,
      status: clamped === last ? "Finished" : "Ready",
    });
  },

  play: () => {
    const s = get();
    const steps = s.result?.steps ?? [];
    if (isEmpty(steps)) return;
    if (s.status === "Finished" || s.status === "Idle" || s.status === "Loading" || s.status === "Error") {
      return;
    }
    set({ status: "Playing", playing: true });
  },

  pause: () => {
    if (!get().playing) return;
    set({ status: "Paused", playing: false });
  },

  restart: () => {
    const steps = get().result?.steps ?? [];
    if (isEmpty(steps)) return;
    set({ activeIndex: 0, playing: false, status: "Ready" });
  },

  setSpeed: (m) => set({ speed: Math.max(0.5, Math.min(4, m)) }),
}));