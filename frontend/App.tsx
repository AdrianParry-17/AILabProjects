import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { ApiError, trafficApi } from "./api";
import { AppShell } from "./components/AppShell";
import { ControlDeck } from "./components/ControlDeck";
import { InsightsPanel } from "./components/InsightsPanel";
import { MapStage } from "./components/MapStage";
import { PlaybackBar } from "./components/PlaybackBar";
import { DEFAULT_WEIGHTS } from "./lib/format";
import type {
  CostWeights,
  GraphPayload,
  MetadataPayload,
  SearchResponse,
  TraceStep,
} from "./types";

const FALLBACK_METADATA: MetadataPayload = {
  algorithms: [
    { id: "bfs", name: "Breadth-First Search", family: "Uninformed", description: "Mở rộng theo từng lớp; tối ưu số cạnh khi mọi cạnh như nhau.", complete: true, optimal: "chỉ theo số cạnh", complexity_time: "O(V + E)", complexity_space: "O(V)" },
    { id: "dfs", name: "Depth-First Search", family: "Uninformed", description: "Đi sâu trước, ít bộ nhớ nhưng rất nhạy với thứ tự lân cận.", complete: true, optimal: false, complexity_time: "O(V + E)", complexity_space: "O(V)" },
    { id: "ucs", name: "Uniform Cost Search", family: "Cost-based", description: "Luôn mở rộng trạng thái có path cost nhỏ nhất.", complete: true, optimal: true, weighted: true, complexity_time: "O((V+E) log V)", complexity_space: "O(V)" },
    { id: "dijkstra", name: "Dijkstra", family: "Cost-based", description: "Single-source shortest path trên trọng số không âm.", complete: true, optimal: true, weighted: true, complexity_time: "O((V+E) log V)", complexity_space: "O(V)" },
    { id: "astar", name: "A* Search", family: "Informed", description: "Kết hợp g(n) đã đi và h(n) ước lượng tới đích.", complete: true, optimal: "với heuristic admissible/consistent", weighted: true, supports_heuristic: true, complexity_time: "worst O(b^d)", complexity_space: "O(V)", caveat: "Optimal khi heuristic không đánh giá quá cao lower bound tương ứng." },
    { id: "greedy_best_first", name: "Greedy Best-First", family: "Informed", description: "Chỉ nhìn h(n); thường nhanh nhưng có thể chọn đường tệ.", complete: "trên finite graph", optimal: false, supports_heuristic: true, complexity_time: "worst O(b^m)", complexity_space: "O(V)" },
    { id: "bidirectional_dijkstra", name: "Bidirectional Dijkstra", family: "Meet-in-the-middle", description: "Tìm từ cả start và goal trên directed reverse graph.", complete: true, optimal: true, weighted: true, complexity_time: "≈ O((V+E) log V)", complexity_space: "O(V)" },
    { id: "ida_star", name: "IDA*", family: "Memory-bounded", description: "Lặp depth-first theo ngưỡng f = g + h.", complete: true, optimal: "với heuristic admissible", supports_heuristic: true, complexity_time: "O(b^d)", complexity_space: "O(d)" },
  ],
  heuristics: [
    { id: "zero", name: "Zero h(n)", description: "A* suy biến thành UCS; baseline an toàn.", admissible: true, consistent: true },
    { id: "haversine", name: "Haversine distance", description: "Khoảng cách đường chim bay tới goal.", admissible: true, consistent: true },
    { id: "travel_time", name: "Optimistic travel time", description: "Haversine chia tốc độ lớn nhất toàn graph.", admissible: true, consistent: true },
    { id: "traffic_aware", name: "Traffic-aware prediction", description: "Nhanh trong thực tế mô phỏng nhưng có thể overestimate.", admissible: false, consistent: false },
  ],
  objectives: [
    { id: "balanced", name: "Balanced cost" },
    { id: "distance", name: "Ngắn nhất theo khoảng cách" },
    { id: "time", name: "Nhanh nhất theo ETA" },
    { id: "safety", name: "Rủi ro thấp nhất" },
    { id: "priority_delivery", name: "Giao ưu tiên" },
  ],
  scenarios: [
    { id: "normal", name: "Bình thường" },
    { id: "morning_rush", name: "Cao điểm buổi sáng" },
    { id: "evening_rush", name: "Cao điểm buổi chiều" },
    { id: "heavy_rain", name: "Mưa lớn / ngập cục bộ" },
    { id: "incident", name: "Sự cố & đóng đường" },
  ],
  defaults: { algorithm: "astar", heuristic: "travel_time", objective: "balanced", scenario: "normal", weights: DEFAULT_WEIGHTS },
};

function errorMessage(error: unknown): string | undefined {
  if (!error) return undefined;
  if (error instanceof ApiError) {
    if (error.status === 422) return "Cấu hình chưa hợp lệ. Hãy kiểm tra điểm đi và điểm đến.";
    if (error.status === 404) return "Không tìm thấy dữ liệu phù hợp cho lựa chọn này.";
    if (error.status >= 500) return "Search engine đang gặp sự cố. Vui lòng thử lại sau ít phút.";
  }
  return "Không thể kết nối với search engine. Hãy kiểm tra backend rồi thử lại.";
}

function safeNodeName(name?: string): string {
  if (!name || /^osm[_\s-]/i.test(name) || /giao\s+lộ\s+osm\s+\d+/i.test(name)) return "Giao lộ chưa đặt tên";
  return name;
}

export default function App() {
  const [start, setStart] = useState("");
  const [goal, setGoal] = useState("");
  const [algorithm, setAlgorithm] = useState("astar");
  const [heuristic, setHeuristic] = useState("travel_time");
  const [objective, setObjective] = useState("balanced");
  const [scenario, setScenario] = useState("normal");
  const [weights, setWeights] = useState<CostWeights>(DEFAULT_WEIGHTS);
  const [selectionTarget, setSelectionTarget] = useState<"start" | "goal">("start");
  const [routeResult, setRouteResult] = useState<SearchResponse>();
  const [traceIndex, setTraceIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(70);

  const healthQuery = useQuery({ queryKey: ["health"], queryFn: trafficApi.health, retry: 1, refetchInterval: 30_000 });
  const metadataQuery = useQuery({ queryKey: ["metadata"], queryFn: trafficApi.metadata });
  const metadata = metadataQuery.data || FALLBACK_METADATA;
  const graphQuery = useQuery({
    queryKey: ["graph", "topology"],
    queryFn: () => trafficApi.graph("normal"),
    staleTime: Infinity,
  });
  const trafficQuery = useQuery({
    queryKey: ["traffic", scenario],
    queryFn: () => trafficApi.traffic(scenario),
    enabled: scenario !== "normal",
    staleTime: 5 * 60_000,
  });
  const graphSnapshot = graphQuery.data;
  const [graph, setGraph] = useState<GraphPayload>();
  const graphError = graphQuery.error || trafficQuery.error;
  const graphLoading = !graph || graphQuery.isFetching || (scenario !== "normal" && trafficQuery.isFetching);

  useEffect(() => {
    if (!graphSnapshot?.nodes.length) return;
    let cancelled = false;
    const frame = window.requestAnimationFrame(() => {
      if (cancelled) return;
      const primaryDeliveryPoints = graphSnapshot.nodes.filter(
      (node) => node.is_delivery_point && node.routing_component === "primary",
      );
      const recommendedStart = String(graphSnapshot.stats?.recommended_start_id || "");
      const recommendedGoal = String(graphSnapshot.stats?.recommended_goal_id || "");
      const pickup = graphSnapshot.nodes.find((node) => node.id === recommendedStart)
        || primaryDeliveryPoints[0]
        || graphSnapshot.nodes[0];
      const dropoff = graphSnapshot.nodes.find((node) => node.id === recommendedGoal)
        || primaryDeliveryPoints.find((node) => node.id !== pickup.id)
        || graphSnapshot.nodes.find((node) => node.id !== pickup.id);
      setStart((current) => graphSnapshot.nodes.some((node) => node.id === current) ? current : pickup.id);
      if (dropoff) {
        setGoal((current) => graphSnapshot.nodes.some((node) => node.id === current && node.id !== pickup.id) ? current : dropoff.id);
      }
      setGraph(graphSnapshot);
    });
    return () => {
      cancelled = true;
      window.cancelAnimationFrame(frame);
    };
  }, [graphSnapshot]);

  const baseRequest = { start, goal, algorithm, heuristic, objective, scenario, weights, trace: true };
  const routeFingerprint = JSON.stringify(baseRequest);
  const currentRequestRef = useRef({ route: routeFingerprint });
  currentRequestRef.current = { route: routeFingerprint };
  const submittedRequestRef = useRef({ route: "" });

  const routeMutation = useMutation({
    mutationFn: () => trafficApi.search(baseRequest),
    onSuccess: (data) => {
      if (submittedRequestRef.current.route !== currentRequestRef.current.route) return;
      setRouteResult(data);
      setTraceIndex(0);
      setPlaying(Boolean(data.trace.length));
    },
  });

  const trace = useMemo<TraceStep[]>(() => {
    if (!routeResult) return [];
    const nameById = new Map(graph?.nodes.map((node) => [node.id, safeNodeName(node.name)]) || []);
    const enrich = (steps: TraceStep[]) => steps.map((step) => {
      const currentName = nameById.get(step.current) || safeNodeName(step.current_name);
      const discoveredCount = step.newly_discovered?.length || 0;
      const reason = step.phase === "start"
        ? `Khởi tạo frontier tại ${currentName}.`
        : step.phase === "finish"
          ? step.found === false
            ? "Đã duyệt hết không gian tìm kiếm nhưng chưa có tuyến khả dụng."
            : `Đã tới ${currentName}; hoàn tất tìm kiếm và dựng lại tuyến đường.`
          : step.phase === "iteration"
            ? "Tăng ngưỡng tìm kiếm và bắt đầu vòng lặp sâu tiếp theo."
            : `Mở rộng ${currentName}; cập nhật ${discoveredCount} hướng đi tiềm năng.`;
      return {
        ...step,
        current_name: currentName,
        reason,
      };
    });
    return enrich(routeResult.trace || []);
  }, [routeResult, graph]);

  const traceIndexRef = useRef(traceIndex);
  traceIndexRef.current = traceIndex;
  useEffect(() => {
    if (!playing || trace.length < 2) return;
    const lengthScale = trace.length > 700 ? 0.34 : trace.length > 400 ? 0.5 : trace.length > 220 ? 0.68 : 1;
    const millisecondsPerStep = Math.max(7, playbackSpeed * lengthScale);
    const visualCadenceMs = trace.length > 220 ? 80 : millisecondsPerStep;
    let frame = 0;
    let previousTime = performance.now();
    let previousVisualTime = previousTime;
    let accumulated = 0;
    let logicalIndex = traceIndexRef.current;
    const advancePlayback = (currentTime: number) => {
      accumulated += Math.min(500, currentTime - previousTime);
      previousTime = currentTime;
      const stepCount = Math.floor(accumulated / millisecondsPerStep);
      if (stepCount > 0) {
        accumulated -= stepCount * millisecondsPerStep;
        logicalIndex = Math.min(trace.length - 1, logicalIndex + stepCount);
        if (currentTime - previousVisualTime >= visualCadenceMs || logicalIndex >= trace.length - 1) {
          previousVisualTime = currentTime;
          traceIndexRef.current = logicalIndex;
          setTraceIndex(logicalIndex);
        }
        if (logicalIndex >= trace.length - 1) {
          setPlaying(false);
          return;
        }
      }
      frame = window.requestAnimationFrame(advancePlayback);
    };
    frame = window.requestAnimationFrame(advancePlayback);
    return () => window.cancelAnimationFrame(frame);
  }, [playing, playbackSpeed, trace.length]);

  useEffect(() => {
    setPlaying(false);
    setTraceIndex(0);
    setRouteResult(undefined);
  }, [start, goal, algorithm, heuristic, objective, scenario, weights.distance, weights.time, weights.congestion, weights.risk]);

  const handleMapSelect = useCallback((id: string) => {
    if (selectionTarget === "start") {
      setStart(id);
      setSelectionTarget("goal");
    } else if (id !== start) {
      setGoal(id);
    }
  }, [selectionTarget, start]);

  const handleObjective = useCallback((next: string) => {
    setObjective(next);
    const presets: Record<string, CostWeights> = {
  balanced: {
    distance: 0.25,
    time: 0.35,
    congestion: 0.25,
    risk: 0.15,
  },

  distance: {
    distance: 1.0,
    time: 0.0,
    congestion: 0.0,
    risk: 0.0,
  },

  time: {
    distance: 0.10,
    time: 0.55,
    congestion: 0.30,
    risk: 0.05,
  },

  safety: {
    distance: 0.15,
    time: 0.15,
    congestion: 0.10,
    risk: 0.60,
  },

  priority_delivery: {
    distance: 0.15,
    time: 0.45,
    congestion: 0.30,
    risk: 0.10,
  },
};
    if (presets[next]) setWeights(presets[next]);
  }, []);

  const handleWeights = useCallback((next: CostWeights) => {
    setWeights(next);
    setObjective("custom");
  }, []);

  const run = useCallback(() => {
    setPlaying(false);
    submittedRequestRef.current.route = routeFingerprint;
    routeMutation.mutate();
  }, [routeFingerprint, routeMutation.mutate]);

  const activeMutation = routeMutation;
  const scenarioName = metadata.scenarios.find((item) => item.id === scenario)?.name || scenario;
  const nodeNames = useMemo(() => new Map((graph?.nodes || []).map((node) => [node.id, safeNodeName(node.name)] as const)), [graph]);
  const selectedPathNames = useMemo(() => {
    if (!routeResult || !graph) return undefined;
    return routeResult.path.map((id) => nodeNames.get(id) || safeNodeName(id));
  }, [routeResult, nodeNames]);

  return (
    <AppShell online={healthQuery.isSuccess} scenarioName={scenarioName}>
      <AnimatePresence mode="wait">
        <motion.main
          key="route"
          className="workspace-grid"
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -5 }}
          transition={{ duration: 0.2 }}
        >
          <ControlDeck
            graph={graph}
            metadata={metadata}
            start={start}
            goal={goal}
            algorithm={algorithm}
            heuristic={heuristic}
            objective={objective}
            scenario={scenario}
            weights={weights}
            selectionTarget={selectionTarget}
            loading={activeMutation.isPending}
            error={errorMessage(activeMutation.error)}
            onStart={setStart}
            onGoal={setGoal}
            onAlgorithm={setAlgorithm}
            onHeuristic={setHeuristic}
            onObjective={handleObjective}
            onScenario={setScenario}
            onWeights={handleWeights}
            onSelectionTarget={setSelectionTarget}
            onRun={run}
          />

          <div className="map-column">
            {graphError && (
              <div className="graph-error panel">
                <AlertTriangle size={19} />
                <span><strong>Không tải được mạng giao thông.</strong>{errorMessage(graphError)}</span>
                <button type="button" onClick={() => { graphQuery.refetch(); if (scenario !== "normal") trafficQuery.refetch(); }}><RefreshCw size={14} /> Thử lại</button>
              </div>
            )}
            <MapStage
              graph={graph}
              result={routeResult}
              traceStep={trace[traceIndex]}
              start={start}
              goal={goal}
              selectionLabel={selectionTarget === "start" ? "Đang chọn điểm đi" : "Đang chọn điểm đến"}
              onSelectNode={handleMapSelect}
              loading={graphLoading}
              trafficOverlay={trafficQuery.data?.scenario === scenario ? trafficQuery.data : undefined}
            />
            <PlaybackBar
              trace={trace}
              index={traceIndex}
              playing={playing}
              speed={playbackSpeed}
              algorithm={routeResult?.algorithm || algorithm}
              nodeNames={nodeNames}
              onIndex={setTraceIndex}
              onPlaying={setPlaying}
              onSpeed={setPlaybackSpeed}
            />
          </div>

          <InsightsPanel result={routeResult} selectedPathNames={selectedPathNames} />
        </motion.main>
      </AnimatePresence>
    </AppShell>
  );
}