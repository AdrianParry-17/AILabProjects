import type { CSSProperties } from "react";
import { Activity, Layers3, Pause, Play, RotateCcw, SkipBack, SkipForward, StepForward } from "lucide-react";
import type { TraceStep } from "../types";

interface Props {
  trace: TraceStep[];
  index: number;
  playing: boolean;
  speed: number;
  onIndex: (index: number) => void;
  onPlaying: (playing: boolean) => void;
  onSpeed: (speed: number) => void;
}

export function PlaybackBar({ trace, index, playing, speed, onIndex, onPlaying, onSpeed }: Props) {
  const step = trace[index];
  const last = Math.max(trace.length - 1, 0);
  const progress = trace.length > 1 ? (index / last) * 100 : 0;

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
