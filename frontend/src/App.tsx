import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { ApiError, trafficApi } from "./api";
import { AppShell } from "./components/AppShell";
import { AlgorithmGuide } from "./components/AlgorithmGuide";
import { ComparePanel } from "./components/ComparePanel";
import { ControlDeck } from "./components/ControlDeck";
import { InsightsPanel } from "./components/InsightsPanel";
import { MapStage } from "./components/MapStage";
import { ModeTabs } from "./components/ModeTabs";
import { PlaybackBar } from "./components/PlaybackBar";
import { DEFAULT_WEIGHTS } from "./lib/format";
import type {
  CompareResponse,
  CostWeights,
  GraphPayload,
  MetadataPayload,
  MultiRouteResponse,
  PlannerMode,
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
  multi_algorithms: [
    { id: "nearest_neighbor", name: "Nearest Neighbor", description: "Heuristic tham lam chọn điểm gần nhất.", complete: true, optimal: false },
    { id: "two_opt", name: "Nearest Neighbor + 2-opt", description: "Heuristic nhanh rồi cải thiện cục bộ.", complete: true, optimal: false },
    { id: "held_karp", name: "Held–Karp exact", description: "Dynamic programming tối ưu cho tối đa 10 stops.", complete: true, optimal: true },
    { id: "simulated_annealing", name: "Simulated Annealing", description: "Metaheuristic thoát local optimum.", complete: true, optimal: false },
  ],
  defaults: { algorithm: "astar", heuristic: "travel_time", objective: "balanced", scenario: "normal", weights: DEFAULT_WEIGHTS },
};

function errorMessage(error: unknown): string | undefined {
  if (!error) return undefined;
  if (error instanceof ApiError) {
    if (error.status === 422) return "Cấu hình chưa hợp lệ. Hãy kiểm tra điểm đi, điểm đến và các điểm ghé.";
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
  const [mode, setMode] = useState<PlannerMode>("route");
  const [start, setStart] = useState("");
  const [goal, setGoal] = useState("");
  const [stops, setStops] = useState<string[]>([]);
  const [algorithm, setAlgorithm] = useState("astar");
  const [heuristic, setHeuristic] = useState("travel_time");
  const [objective, setObjective] = useState("balanced");
  const [scenario, setScenario] = useState("normal");
  const [weights, setWeights] = useState<CostWeights>(DEFAULT_WEIGHTS);
  const [selectionTarget, setSelectionTarget] = useState<"start" | "goal" | "stop">("start");
  const [comparisonAlgorithms, setComparisonAlgorithms] = useState(["bfs", "ucs", "astar", "greedy_best_first"]);
  const [multiMethod, setMultiMethod] = useState("two_opt");
  const [returnToStart, setReturnToStart] = useState(false);
  const [routeResult, setRouteResult] = useState<SearchResponse>();
  const [compareResult, setCompareResult] = useState<CompareResponse>();
  const [multiResult, setMultiResult] = useState<MultiRouteResponse>();
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
  const compareFingerprint = JSON.stringify({ ...baseRequest, algorithms: comparisonAlgorithms });
  const multiFingerprint = JSON.stringify({ start, stops, returnToStart, multiMethod, algorithm, heuristic, objective, scenario, weights });
  const currentRequestRef = useRef({ route: routeFingerprint, compare: compareFingerprint, multi: multiFingerprint });
  currentRequestRef.current = { route: routeFingerprint, compare: compareFingerprint, multi: multiFingerprint };
  const submittedRequestRef = useRef({ route: "", compare: "", multi: "" });

  const routeMutation = useMutation({
    mutationFn: () => trafficApi.search(baseRequest),
    onSuccess: (data) => {
      if (submittedRequestRef.current.route !== currentRequestRef.current.route) return;
      setRouteResult(data);
      setTraceIndex(0);
      setPlaying(Boolean(data.trace.length));
    },
  });
  const compareMutation = useMutation({
    mutationFn: () => trafficApi.compare({ ...baseRequest, algorithms: comparisonAlgorithms }),
    onSuccess: (data) => {
      if (submittedRequestRef.current.compare !== currentRequestRef.current.compare) return;
      setCompareResult(data);
      setTraceIndex(0);
      setPlaying(false);
    },
  });
  const multiMutation = useMutation({
    mutationFn: () => trafficApi.multiRoute({
      start,
      stops,
      return_to_start: returnToStart,
      method: multiMethod,
      segment_algorithm: algorithm,
      heuristic,
      objective,
      scenario,
      weights,
    }),
    onSuccess: (data) => {
      if (submittedRequestRef.current.multi !== currentRequestRef.current.multi) return;
      setMultiResult(data);
      setTraceIndex(0);
      setPlaying(false);
    },
  });

  const displayResult = useMemo<SearchResponse | MultiRouteResponse | undefined>(() => {
    if (mode === "multi") return multiResult;
    if (mode === "compare") {
      if (!compareResult?.results.length) return undefined;
      return compareResult.results.find((item) => item.algorithm === compareResult.winner) || compareResult.results[0];
    }
    return routeResult;
  }, [mode, routeResult, compareResult, multiResult]);

  const trace = useMemo<TraceStep[]>(() => {
    if (!displayResult) return [];
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
    if ("trace" in displayResult) return enrich(displayResult.trace || []);
    if ("segments" in displayResult) return [];
    return [];
  }, [displayResult, graph]);

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
    setCompareResult(undefined);
    setMultiResult(undefined);
  }, [start, goal, stops.join("|"), algorithm, heuristic, objective, scenario, weights.distance, weights.time, weights.congestion, weights.risk, comparisonAlgorithms.join("|"), multiMethod, returnToStart]);

  useEffect(() => {
    setPlaying(false);
    setTraceIndex(0);
  }, [mode]);

  const handleMapSelect = useCallback((id: string) => {
    if (selectionTarget === "start") {
      setStart(id);
      setSelectionTarget(mode === "multi" ? "stop" : "goal");
    } else if (selectionTarget === "goal") {
      if (id !== start) setGoal(id);
    } else if (id !== start) {
      const stopLimit = multiMethod === "held_karp" ? 10 : 12;
      setStops((current) => current.includes(id) ? current.filter((item) => item !== id) : current.length < stopLimit ? [...current, id] : current);
    }
  }, [selectionTarget, mode, start, multiMethod]);

  const handleMode = useCallback((next: PlannerMode) => {
    setMode(next);
    setSelectionTarget(next === "multi" ? "stop" : "start");
  }, []);

  const handleObjective = useCallback((next: string) => {
    setObjective(next);
    const presets: Record<string, CostWeights> = {
      balanced: { distance: 1, time: 1.35, congestion: 2.2, risk: 3.4 },
      distance: { distance: 5, time: 0.4, congestion: 0.2, risk: 0.2 },
      time: { distance: 0.4, time: 5, congestion: 2.8, risk: 0.4 },
      safety: { distance: 0.4, time: 1, congestion: 1.7, risk: 5 },
      priority_delivery: { distance: 0.7, time: 5, congestion: 3.2, risk: 2.2 },
    };
    if (presets[next]) setWeights(presets[next]);
  }, []);

  const handleWeights = useCallback((next: CostWeights) => {
    setWeights(next);
    setObjective("custom");
  }, []);

  const run = useCallback(() => {
    setPlaying(false);
    if (mode === "compare") {
      submittedRequestRef.current.compare = compareFingerprint;
      compareMutation.mutate();
    } else if (mode === "multi") {
      submittedRequestRef.current.multi = multiFingerprint;
      multiMutation.mutate();
    } else {
      submittedRequestRef.current.route = routeFingerprint;
      routeMutation.mutate();
    }
  }, [mode, compareFingerprint, multiFingerprint, routeFingerprint, compareMutation.mutate, multiMutation.mutate, routeMutation.mutate]);

  const activeMutation = mode === "compare" ? compareMutation : mode === "multi" ? multiMutation : routeMutation;
  const scenarioName = metadata.scenarios.find((item) => item.id === scenario)?.name || scenario;
  const selectedPathNames = useMemo(() => {
    if (!displayResult || !graph) return undefined;
    const nameById = new Map(graph.nodes.map((node) => [node.id, node.name]));
    if ("order" in displayResult) {
      const ids = [start, ...displayResult.order, ...(returnToStart ? [start] : [])];
      return ids.map((id) => safeNodeName(nameById.get(id)));
    }
    return displayResult.path.map((id) => safeNodeName(nameById.get(id)));
  }, [displayResult, graph, start, returnToStart]);
  const deliveryLegs = useMemo(() => {
    if (mode !== "multi" || !multiResult || !graph) return [];
    const nameById = new Map(graph.nodes.map((node) => [node.id, safeNodeName(node.name)]));
    return multiResult.segments.map((segment, index) => ({
      index: index + 1,
      from: nameById.get(segment.from_id) || "Điểm giao nhận",
      to: nameById.get(segment.to_id) || "Điểm giao nhận",
      distanceM: segment.distance_m || 0,
      timeMin: segment.travel_time_min || 0,
      cost: segment.total_cost || 0,
    }));
  }, [graph, mode, multiResult]);

  return (
    <AppShell online={healthQuery.isSuccess} scenarioName={scenarioName}>
      <ModeTabs value={mode} onChange={handleMode} />

      {mode === "learn" ? (
        <AlgorithmGuide metadata={metadata} />
      ) : (
        <AnimatePresence mode="wait">
          <motion.main
            key={mode}
            className="workspace-grid"
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            transition={{ duration: 0.2 }}
          >
            <ControlDeck
              mode={mode}
              graph={graph}
              metadata={metadata}
              start={start}
              goal={goal}
              stops={stops}
              algorithm={algorithm}
              heuristic={heuristic}
              objective={objective}
              scenario={scenario}
              weights={weights}
              selectionTarget={selectionTarget}
              comparisonAlgorithms={comparisonAlgorithms}
              multiMethod={multiMethod}
              returnToStart={returnToStart}
              loading={activeMutation.isPending}
              error={errorMessage(activeMutation.error)}
              onStart={setStart}
              onGoal={setGoal}
              onStops={setStops}
              onAlgorithm={setAlgorithm}
              onHeuristic={setHeuristic}
              onObjective={handleObjective}
              onScenario={setScenario}
              onWeights={handleWeights}
              onSelectionTarget={setSelectionTarget}
              onComparisonAlgorithms={setComparisonAlgorithms}
              onMultiMethod={setMultiMethod}
              onReturnToStart={setReturnToStart}
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
                result={displayResult}
                traceStep={mode === "compare" && !playing && traceIndex === 0 ? undefined : trace[traceIndex]}
                start={start}
                goal={mode === "multi" ? undefined : goal}
                stops={mode === "multi" ? stops : []}
                selectionLabel={selectionTarget === "start" ? "Đang chọn điểm đi" : selectionTarget === "goal" ? "Đang chọn điểm đến" : "Đang thêm điểm ghé"}
                onSelectNode={handleMapSelect}
                loading={graphLoading}
                trafficOverlay={trafficQuery.data?.scenario === scenario ? trafficQuery.data : undefined}
              />
              <PlaybackBar
                trace={trace}
                index={traceIndex}
                playing={playing}
                speed={playbackSpeed}
                onIndex={setTraceIndex}
                onPlaying={setPlaying}
                onSpeed={setPlaybackSpeed}
              />
            </div>

            {mode === "compare"
              ? <ComparePanel data={compareResult} metadata={metadata} />
              : <InsightsPanel result={displayResult} selectedPathNames={selectedPathNames} deliveryLegs={deliveryLegs} />}
          </motion.main>
        </AnimatePresence>
      )}
    </AppShell>
  );
}
