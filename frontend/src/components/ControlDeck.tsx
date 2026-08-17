import { memo, useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowDownUp,
  BrainCircuit,
  Check,
  ChevronRight,
  CircleDot,
  Gauge,
  ListPlus,
  LocateFixed,
  Play,
  RotateCcw,
  Settings2,
  Shield,
  Sparkles,
  Target,
  X,
} from "lucide-react";
import type {
  AlgorithmMeta,
  CostWeights,
  GraphPayload,
  MetadataPayload,
  PlannerMode,
} from "../types";
import { formatNodeKind } from "../lib/format";

type SelectionTarget = "start" | "goal" | "stop";
const LOCATION_OPTION_BATCH = 32;
const PICKUP_ICON = <LocateFixed size={18} />;
const DROPOFF_ICON = <Target size={18} />;

interface Props {
  mode: PlannerMode;
  graph?: GraphPayload;
  metadata: MetadataPayload;
  start: string;
  goal: string;
  stops: string[];
  algorithm: string;
  heuristic: string;
  objective: string;
  scenario: string;
  weights: CostWeights;
  selectionTarget: SelectionTarget;
  comparisonAlgorithms: string[];
  multiMethod: string;
  returnToStart: boolean;
  loading: boolean;
  error?: string;
  onStart: (value: string) => void;
  onGoal: (value: string) => void;
  onStops: (value: string[]) => void;
  onAlgorithm: (value: string) => void;
  onHeuristic: (value: string) => void;
  onObjective: (value: string) => void;
  onScenario: (value: string) => void;
  onWeights: (value: CostWeights) => void;
  onSelectionTarget: (value: SelectionTarget) => void;
  onComparisonAlgorithms: (value: string[]) => void;
  onMultiMethod: (value: string) => void;
  onReturnToStart: (value: boolean) => void;
  onRun: () => void;
}

const LocationSelect = memo(function LocationSelect({
  label,
  icon,
  value,
  graph,
  deliveryPoints,
  active,
  onActivate,
  onChange,
}: {
  label: string;
  icon: React.ReactNode;
  value: string;
  graph?: GraphPayload;
  deliveryPoints: GraphPayload["nodes"];
  active: boolean;
  onActivate: () => void;
  onChange: (value: string) => void;
}) {
  const options = useMemo(() => {
    if (!graph) return deliveryPoints;
    const selected = graph.nodes.find((node) => node.id === value);
    return selected && !deliveryPoints.some((node) => node.id === selected.id)
      ? [selected, ...deliveryPoints]
      : deliveryPoints;
  }, [deliveryPoints, graph, value]);
  return (
    <label className={`location-field ${active ? "active" : ""}`} onClick={onActivate}>
      <span className="location-icon">{icon}</span>
      <span className="field-copy">
        <span className="field-label">{label}</span>
        <select value={value} onChange={(event) => onChange(event.target.value)}>
          <option value="">Chọn điểm giao nhận hoặc bấm bản đồ…</option>
          {options.map((node) => (
            <option key={node.id} value={node.id}>{node.name} · {formatNodeKind(node.kind)}</option>
          ))}
        </select>
      </span>
      <ChevronRight size={16} />
    </label>
  );
});

function WeightSlider({
  label,
  value,
  color,
  onChange,
}: {
  label: string;
  value: number;
  color: string;
  onChange: (value: number) => void;
}) {
  return (
    <label className="weight-slider">
      <span><i style={{ background: color }} /> {label}</span>
      <input type="range" min={0} max={5} step={0.1} value={value} onChange={(event) => onChange(Number(event.target.value))} />
      <output>{value.toFixed(1)}</output>
    </label>
  );
}

function GuaranteeBadge({ algorithm }: { algorithm?: AlgorithmMeta }) {
  if (!algorithm) return null;
  const statement = String(algorithm.optimal).toLowerCase();
  const optimal = algorithm.optimal === true || statement.startsWith("optimal for");
  const conditional = statement.startsWith("optimal with");
  return (
    <div className={`guarantee-note ${optimal ? "guaranteed" : "conditional"}`}>
      {optimal ? <Shield size={15} /> : <AlertTriangle size={15} />}
      <span>
        <strong>{optimal ? "Bảo đảm tối ưu" : conditional ? "Bảo đảm có điều kiện" : "Không bảo đảm tối ưu"}</strong>
        {algorithm.caveat || algorithm.description}
      </span>
    </div>
  );
}

export const ControlDeck = memo(function ControlDeck(props: Props) {
  const {
    mode, graph, metadata, start, goal, stops, algorithm, heuristic, objective, scenario, weights,
    selectionTarget, comparisonAlgorithms, multiMethod, returnToStart, loading, error,
  } = props;
  const selectedAlgorithm = metadata.algorithms.find((item) => item.id === algorithm);
  const supportsHeuristic = selectedAlgorithm?.supports_heuristic ?? ["astar", "greedy_best_first", "ida_star"].includes(algorithm);
  const canRun = Boolean(start && (mode === "multi" ? stops.length >= 2 : goal));
  const deliveryPoints = useMemo(() => graph?.nodes
    .filter((node) => node.is_delivery_point && node.routing_component === "primary")
    .sort((first, second) => first.name.localeCompare(second.name, "vi")) || [], [graph]);
  const [visibleDeliveryPointCount, setVisibleDeliveryPointCount] = useState(0);
  useEffect(() => {
    let cancelled = false;
    let frame = 0;
    let nextCount = Math.min(LOCATION_OPTION_BATCH, deliveryPoints.length);
    setVisibleDeliveryPointCount(0);
    const revealNextBatch = () => {
      if (cancelled) return;
      setVisibleDeliveryPointCount(nextCount);
      if (nextCount < deliveryPoints.length) {
        nextCount = Math.min(deliveryPoints.length, nextCount + LOCATION_OPTION_BATCH);
        frame = window.requestAnimationFrame(revealNextBatch);
      }
    };
    if (deliveryPoints.length) frame = window.requestAnimationFrame(revealNextBatch);
    return () => {
      cancelled = true;
      window.cancelAnimationFrame(frame);
    };
  }, [deliveryPoints]);
  const visibleDeliveryPoints = useMemo(
    () => deliveryPoints.slice(0, visibleDeliveryPointCount),
    [deliveryPoints, visibleDeliveryPointCount],
  );
  const activateStart = useCallback(() => props.onSelectionTarget("start"), [props.onSelectionTarget]);
  const activateGoal = useCallback(() => props.onSelectionTarget("goal"), [props.onSelectionTarget]);
  const stopLimit = multiMethod === "held_karp" ? 10 : 12;
  const availableStops = useMemo(
    () => deliveryPoints.filter((node) => node.id !== start && !stops.includes(node.id)),
    [deliveryPoints, start, stops],
  );

  const setWeight = (key: keyof CostWeights, value: number) => props.onWeights({ ...weights, [key]: value });
  const toggleCompare = (id: string) => {
    const next = comparisonAlgorithms.includes(id)
      ? comparisonAlgorithms.filter((item) => item !== id)
      : [...comparisonAlgorithms, id];
    if (next.length >= 2 && next.length <= 8) props.onComparisonAlgorithms(next);
  };

  return (
    <aside className="control-deck panel">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">DELIVERY CONFIGURATION</span>
          <h2>{mode === "multi" ? "Tối ưu vòng giao hàng" : mode === "compare" ? "Benchmark thuật toán" : "Lập tuyến giao nhận"}</h2>
        </div>
        <button className="icon-button" type="button" title="Đặt lại trọng số" onClick={() => props.onWeights({ distance: 1, time: 1.35, congestion: 2.2, risk: 3.4 })}>
          <RotateCcw size={16} />
        </button>
      </div>

      <div className="location-stack">
        <LocationSelect
          label="Điểm lấy hàng / xuất phát"
           icon={PICKUP_ICON}
          value={start}
          graph={graph}
           deliveryPoints={visibleDeliveryPoints}
          active={selectionTarget === "start"}
           onActivate={activateStart}
          onChange={props.onStart}
        />

        {mode !== "multi" && (
          <>
            <button
              type="button"
              className="swap-button"
              title="Đảo chiều tuyến"
              onClick={() => { props.onStart(goal); props.onGoal(start); }}
            >
              <ArrowDownUp size={14} />
            </button>
            <LocationSelect
              label="Điểm giao hàng / đích"
               icon={DROPOFF_ICON}
              value={goal}
              graph={graph}
               deliveryPoints={visibleDeliveryPoints}
              active={selectionTarget === "goal"}
               onActivate={activateGoal}
              onChange={props.onGoal}
            />
          </>
        )}
      </div>

      {mode === "multi" && (
        <div className="multi-stops-block">
          <div className="subheading-row">
            <span><ListPlus size={15} /> Điểm cần ghé ({stops.length})</span>
            <button type="button" className={selectionTarget === "stop" ? "is-active" : ""} onClick={() => props.onSelectionTarget("stop")}>
              + chọn trên map
            </button>
          </div>
          <label className="compact-field stop-picker">
            <span>Thêm điểm giao từ danh sách</span>
            <select
              aria-label="Thêm điểm giao"
              value=""
              disabled={stops.length >= stopLimit || !availableStops.length}
              onChange={(event) => {
                const id = event.target.value;
                if (id && stops.length < stopLimit) props.onStops([...stops, id]);
              }}
            >
              <option value="">Chọn địa điểm giao nhận…</option>
              {availableStops.map((node) => <option key={node.id} value={node.id}>{node.name} · {formatNodeKind(node.kind)}</option>)}
            </select>
          </label>
          <div className="stop-chips">
            {!stops.length && <span className="empty-note">Thêm 2–12 điểm giao; Held–Karp hỗ trợ tối đa 10.</span>}
            {stops.map((id, index) => {
              const node = graph?.nodes.find((item) => item.id === id);
              return (
                <span key={id} className="stop-chip">
                  <b>{index + 1}</b>{node?.short_name || node?.name || id}
                  <button type="button" onClick={() => props.onStops(stops.filter((item) => item !== id))}><X size={12} /></button>
                </span>
              );
            })}
          </div>
          <div className="two-column-fields">
            <label className="compact-field">
              <span>Optimizer</span>
              <select value={multiMethod} onChange={(event) => props.onMultiMethod(event.target.value)}>
                {(metadata.multi_algorithms || []).map((item) => <option key={item.id} value={item.id} disabled={item.id === "held_karp" && stops.length > 10}>{item.name}</option>)}
                {!(metadata.multi_algorithms || []).length && <>
                  <option value="nearest_neighbor">Nearest Neighbor</option>
                  <option value="two_opt">Nearest Neighbor + 2-opt</option>
                  <option value="held_karp">Held–Karp exact</option>
                  <option value="simulated_annealing">Simulated Annealing</option>
                </>}
              </select>
            </label>
            <label className="toggle-field">
              <input type="checkbox" checked={returnToStart} onChange={(event) => props.onReturnToStart(event.target.checked)} />
              <span className="toggle-track"><i /></span>
              Quay về điểm đầu
            </label>
          </div>
        </div>
      )}

      <div className="divider" />

      <div className="control-grid">
        {mode !== "compare" && mode !== "multi" && (
          <label className="compact-field span-2">
            <span><BrainCircuit size={14} /> Thuật toán</span>
            <select value={algorithm} onChange={(event) => props.onAlgorithm(event.target.value)}>
              {metadata.algorithms.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
        )}

        {mode === "compare" && (
          <div className="algorithm-picker span-2">
            <span className="field-label"><BrainCircuit size={14} /> Chọn 2–8 thuật toán</span>
            <div className="algorithm-check-grid">
              {metadata.algorithms.map((item) => {
                const selected = comparisonAlgorithms.includes(item.id);
                return (
                  <button key={item.id} type="button" className={selected ? "selected" : ""} onClick={() => toggleCompare(item.id)}>
                    <span className="check-box">{selected && <Check size={12} />}</span>{item.name}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <label className="compact-field">
          <span><Gauge size={14} /> Mục tiêu</span>
          <select value={objective} onChange={(event) => props.onObjective(event.target.value)}>
            {metadata.objectives.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>

        {mode !== "multi" && (
          <label className="compact-field">
            <span><Sparkles size={14} /> Heuristic</span>
            <select value={heuristic} disabled={!supportsHeuristic && mode !== "compare"} onChange={(event) => props.onHeuristic(event.target.value)}>
              {metadata.heuristics.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </label>
        )}

        <label className="compact-field span-2">
          <span><CircleDot size={14} /> Điều kiện giao thông</span>
          <select value={scenario} onChange={(event) => props.onScenario(event.target.value)}>
            {metadata.scenarios.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
      </div>

      {mode === "multi" && (
        <div className="guarantee-note guaranteed">
          <Shield size={15} />
          <span><strong>Chặng giao dùng Dijkstra</strong>Optimizer chỉ sắp thứ tự điểm ghé; mỗi chặng dùng đường đi chi phí thấp nhất.</span>
        </div>
      )}

      <details className="weight-panel" open>
        <summary><Settings2 size={15} /> Hàm chi phí <span>Σ wᵢ × featureᵢ</span></summary>
        <div className="weight-body">
          <WeightSlider label="Khoảng cách" value={weights.distance} color="#38bdf8" onChange={(value) => setWeight("distance", value)} />
          <WeightSlider label="Thời gian" value={weights.time} color="#34d399" onChange={(value) => setWeight("time", value)} />
          <WeightSlider label="Ùn tắc" value={weights.congestion} color="#fbbf24" onChange={(value) => setWeight("congestion", value)} />
          <WeightSlider label="Rủi ro" value={weights.risk} color="#fb7185" onChange={(value) => setWeight("risk", value)} />
        </div>
      </details>

      {mode !== "compare" && mode !== "multi" && <GuaranteeBadge algorithm={selectedAlgorithm} />}
      {error && <div className="error-banner"><AlertTriangle size={16} /><span>{error}</span></div>}

      <button type="button" className="run-button" onClick={props.onRun} disabled={!canRun || loading || (mode === "compare" && comparisonAlgorithms.length < 2)}>
        {loading ? <span className="spinner" /> : <Play size={18} fill="currentColor" />}
        <span>{loading ? "Đang chạy search engine…" : mode === "compare" ? `Chạy benchmark ${comparisonAlgorithms.length} thuật toán` : mode === "multi" ? "Tối ưu hành trình" : "Tìm tuyến & tạo lời giải thích"}</span>
      </button>
    </aside>
  );
});
