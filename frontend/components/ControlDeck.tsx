import { memo, useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowDownUp,
  BrainCircuit,
  CircleDot,
  Gauge,
  LocateFixed,
  Play,
  RotateCcw,
  Settings2,
  Shield,
  Sparkles,
  Target,
} from "lucide-react";
import type {
  AlgorithmMeta,
  CostWeights,
  GraphPayload,
  MetadataPayload,
} from "../types";
import { formatNodeKind } from "../lib/format";

type SelectionTarget = "start" | "goal";
const LOCATION_OPTION_BATCH = 32;
const PICKUP_ICON = <LocateFixed size={18} />;
const DROPOFF_ICON = <Target size={18} />;

interface Props {
  graph?: GraphPayload;
  metadata: MetadataPayload;
  start: string;
  goal: string;
  algorithm: string;
  heuristic: string;
  objective: string;
  scenario: string;
  weights: CostWeights;
  selectionTarget: SelectionTarget;
  loading: boolean;
  error?: string;
  onStart: (value: string) => void;
  onGoal: (value: string) => void;
  onAlgorithm: (value: string) => void;
  onHeuristic: (value: string) => void;
  onObjective: (value: string) => void;
  onScenario: (value: string) => void;
  onWeights: (value: CostWeights) => void;
  onSelectionTarget: (value: SelectionTarget) => void;
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
    graph, metadata, start, goal, algorithm, heuristic, objective, scenario, weights,
    selectionTarget, loading, error,
  } = props;
  const selectedAlgorithm = metadata.algorithms.find((item) => item.id === algorithm);
  const supportsHeuristic = selectedAlgorithm?.supports_heuristic ?? ["astar", "greedy_best_first", "ida_star"].includes(algorithm);
  const canRun = Boolean(start && goal);
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

  const setWeight = (key: keyof CostWeights, value: number) => props.onWeights({ ...weights, [key]: value });

  return (
    <aside className="control-deck panel">
      <div className="panel-heading">
        <div>
          <span className="section-kicker">DELIVERY CONFIGURATION</span>
          <h2>Lập tuyến giao nhận</h2>
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
      </div>

      <div className="divider" />

      <div className="control-grid">
        <label className="compact-field span-2">
          <span><BrainCircuit size={14} /> Thuật toán</span>
          <select value={algorithm} onChange={(event) => props.onAlgorithm(event.target.value)}>
            {metadata.algorithms.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>

        <label className="compact-field">
          <span><Gauge size={14} /> Mục tiêu</span>
          <select value={objective} onChange={(event) => props.onObjective(event.target.value)}>
            {metadata.objectives.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>

        <label className="compact-field">
          <span><Sparkles size={14} /> Heuristic</span>
          <select value={heuristic} disabled={!supportsHeuristic} onChange={(event) => props.onHeuristic(event.target.value)}>
            {metadata.heuristics.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>

        <label className="compact-field span-2">
          <span><CircleDot size={14} /> Điều kiện giao thông</span>
          <select value={scenario} onChange={(event) => props.onScenario(event.target.value)}>
            {metadata.scenarios.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
      </div>

      <details className="weight-panel" open>
        <summary><Settings2 size={15} /> Hàm chi phí <span>Σ wᵢ × featureᵢ</span></summary>
        <div className="weight-body">
          <WeightSlider label="Khoảng cách" value={weights.distance} color="#38bdf8" onChange={(value) => setWeight("distance", value)} />
          <WeightSlider label="Thời gian" value={weights.time} color="#34d399" onChange={(value) => setWeight("time", value)} />
          <WeightSlider label="Ùn tắc" value={weights.congestion} color="#fbbf24" onChange={(value) => setWeight("congestion", value)} />
          <WeightSlider label="Rủi ro" value={weights.risk} color="#fb7185" onChange={(value) => setWeight("risk", value)} />
        </div>
      </details>

      <GuaranteeBadge algorithm={selectedAlgorithm} />
      {error && <div className="error-banner"><AlertTriangle size={16} /><span>{error}</span></div>}

      <button type="button" className="run-button" onClick={props.onRun} disabled={!canRun || loading}>
        {loading ? <span className="spinner" /> : <Play size={18} fill="currentColor" />}
        <span>{loading ? "Đang chạy search engine…" : "Tìm tuyến & tạo lời giải thích"}</span>
      </button>
    </aside>
  );
});