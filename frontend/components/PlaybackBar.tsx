import type { CSSProperties } from "react";
import { Activity, Layers3, Pause, Play, RotateCcw, SkipBack, SkipForward, StepForward } from "lucide-react";
import type { TraceStep } from "../types";
import { compactNumber } from "../lib/format";

interface Props {
  trace: TraceStep[];
  index: number;
  playing: boolean;
  speed: number;
  algorithm: string;
  nodeNames?: Map<string, string>;
  onIndex: (index: number) => void;
  onPlaying: (playing: boolean) => void;
  onSpeed: (speed: number) => void;
}

type TraceColumn = {
  key: string;
  label: string;
  value: (step: TraceStep, rowIndex: number) => string;
};

function algorithmTraceColumns(algorithm: string, nodeNames?: Map<string, string>): TraceColumn[] {
  const stepColumn: TraceColumn = {
    key: "step",
    label: "Bước",
    value: (_step, rowIndex) => String(rowIndex + 1),
  };
  const nodeColumn: TraceColumn = {
    key: "node",
    label: "Node đang xét",
    value: (step) => step.current_name || step.current || "—",
  };
  const queueColumn: TraceColumn = {
    key: "queue",
    label: "Queue",
    value: (step) => {
      const queue = step.frontier_names?.length ? step.frontier_names : step.frontier;
      if (!queue?.length) return "∅";
      const resolved = queue.map((id) => nodeNames?.get(id) || step.frontier_names?.find((name) => name === id) || id);
      const preview = resolved.slice(0, 4).join(" → ");
      return queue.length > 4 ? `${preview} +${queue.length - 4}` : preview;
    },
  };
  const gColumn: TraceColumn = { key: "g", label: "g(n)", value: (step) => compactNumber(step.g_score) };
  const hColumn: TraceColumn = { key: "h", label: "h(n)", value: (step) => compactNumber(step.h_score) };
  const fColumn: TraceColumn = { key: "f", label: "f(n)", value: (step) => compactNumber(step.f_score) };

  switch (algorithm) {
    case "bfs":
    case "dfs":
      return [stepColumn, nodeColumn, queueColumn];
    case "ucs":
    case "dijkstra":
    case "bidirectional_dijkstra":
      return [stepColumn, nodeColumn, gColumn, queueColumn];
    case "greedy_best_first":
      return [stepColumn, nodeColumn, hColumn, queueColumn];
    case "astar":
    case "ida_star":
      return [stepColumn, nodeColumn, gColumn, hColumn, fColumn, queueColumn];
    default:
      return [stepColumn, nodeColumn, gColumn, hColumn, fColumn, queueColumn];
  }
}

export function PlaybackBar({ trace, index, playing, speed, algorithm, nodeNames, onIndex, onPlaying, onSpeed }: Props) {
  const step = trace[index];
  const last = Math.max(trace.length - 1, 0);
  const progress = trace.length > 1 ? (index / last) * 100 : 0;
  const columns = algorithmTraceColumns(algorithm, nodeNames);

  const moveTo = (next: number) => {
    onPlaying(false);
    onIndex(Math.max(0, Math.min(last, next)));
  };

  const togglePlayback = () => {
    if (!playing && index >= last) onIndex(0);
    onPlaying(!playing);
  };

  const phaseLabel = step?.phase === "finish"
    ? "Hoàn tất tại"
    : step?.phase === "start"
      ? "Khởi hành từ"
      : "Đang mở rộng";

  return (
    <div className="playback panel">
      <div className="playback-controls">
        <button type="button" title="Về đầu" aria-label="Về bước đầu tiên" onClick={() => moveTo(0)} disabled={!trace.length}>
          <RotateCcw size={15} />
        </button>
        <button type="button" title="Lùi một bước mở rộng" aria-label="Lùi một bước mở rộng" onClick={() => moveTo(index - 1)} disabled={index <= 0}>
          <SkipBack size={16} />
        </button>
        <button className="play-button" type="button" title={playing ? "Tạm dừng" : "Phát mô phỏng"} aria-label={playing ? "Tạm dừng mô phỏng" : "Phát mô phỏng"} onClick={togglePlayback} disabled={!trace.length}>
          {playing ? <Pause size={18} /> : <Play size={18} fill="currentColor" />}
        </button>
        <button type="button" title="Tiến một bước mở rộng" aria-label="Tiến một bước mở rộng" onClick={() => moveTo(index + 1)} disabled={index >= last}>
          <StepForward size={16} />
        </button>
        <button type="button" title="Đến kết quả" aria-label="Đi tới kết quả cuối" onClick={() => moveTo(last)} disabled={!trace.length}>
          <SkipForward size={16} />
        </button>
      </div>

      <div className="timeline-wrap">
        <div className="timeline-copy">
          <span>Nhịp <strong>{trace.length ? index + 1 : 0}</strong> / {trace.length}</span>
          <span className="current-node">{step ? `${phaseLabel}: ${step.current_name || "giao lộ đang xét"}` : "Chạy thuật toán để xem mô phỏng"}</span>
        </div>
        <div className="timeline-track" style={{ "--trace-progress": `${progress}%` } as CSSProperties}>
          <input
            aria-label="Tiến trình mô phỏng thuật toán"
            type="range"
            min={0}
            max={last}
            value={Math.min(index, last)}
            onChange={(event) => moveTo(Number(event.target.value))}
            disabled={!trace.length}
          />
        </div>
        <div className="step-reason">{step?.reason || "Cây khám phá, frontier và cạnh đang xét sẽ xuất hiện tại đây."}</div>
      </div>

      <div className="trace-stats" aria-label="Trạng thái tìm kiếm">
        <span title="Số nút đang chờ xét"><Layers3 size={13} /><strong>{step?.frontier_size ?? step?.frontier.length ?? 0}</strong> frontier</span>
        <span title="Số nút đã mở rộng"><Activity size={13} /><strong>{step?.explored_count ?? step?.visited.length ?? 0}</strong> đã mở rộng</span>
      </div>

      <div className="trace-table-shell" aria-label="Bảng minh họa các bước tìm kiếm">
        <div className="trace-table-header">
          <span>Bảng minh họa</span>
          <small>Cột thay đổi theo thuật toán đang chọn: {algorithm}</small>
        </div>
        <div className="trace-table-scroll">
          <table className="trace-table">
            <thead>
              <tr>
                {columns.map((column) => <th key={column.key}>{column.label}</th>)}
              </tr>
            </thead>
            <tbody>
              {trace.length ? trace.map((row, rowIndex) => (
                <tr key={`${row.step}-${row.current}`} data-active={rowIndex === index ? "true" : "false"}>
                  {columns.map((column) => <td key={column.key}>{column.value(row, rowIndex)}</td>)}
                </tr>
              )) : (
                <tr>
                  <td colSpan={columns.length}>Chạy thuật toán để xem bảng minh họa từng bước.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <label className="speed-control">
        <span>Tốc độ</span>
        <select value={speed} onChange={(event) => onSpeed(Number(event.target.value))} aria-label="Tốc độ mô phỏng">
          <option value={180}>Quan sát</option>
          <option value={70}>Nhanh</option>
          <option value={32}>Rất nhanh</option>
          <option value={16}>Turbo</option>
        </select>
      </label>
    </div>
  );
}
