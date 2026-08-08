import {
  Activity,
  AlertTriangle,
  Brain,
  Clock3,
  Cpu,
  Gauge,
  Milestone,
  Route,
  ShieldCheck,
  Sparkles,
  TrafficCone,
} from "lucide-react";
import type { MultiRouteResponse, SearchResponse } from "../types";
import { compactNumber, explanationParts, formatDistance, formatRuntime, formatTime } from "../lib/format";

interface Props {
  result?: SearchResponse | MultiRouteResponse;
  selectedPathNames?: string[];
}

function MetricCard({ icon, label, value, tone }: { icon: React.ReactNode; label: string; value: string; tone: string }) {
  return (
    <div className="metric-card" style={{ "--metric-tone": tone } as React.CSSProperties}>
      <span className="metric-icon">{icon}</span>
      <div><small>{label}</small><strong>{value}</strong></div>
    </div>
  );
}

export function InsightsPanel({ result, selectedPathNames }: Props) {
  const metrics = result?.metrics;
  const explanation = explanationParts(result?.explanation as SearchResponse["explanation"]);
  const pathNames = selectedPathNames || (result && "path_names" in result ? result.path_names : undefined) || (result && "order_names" in result ? result.order_names : undefined) || [];
  const breakdown = result && "cost_breakdown" in result ? result.cost_breakdown : undefined;
  const alternative = result && "alternative" in result ? result.alternative : undefined;
  const found = result?.found;

  return (
    <aside className="insights-panel panel">
      <div className="panel-heading compact">
        <div>
          <span className="section-kicker">ROUTE INTELLIGENCE</span>
          <h2>Phân tích kết quả</h2>
        </div>
        <span className={`status-pill ${found ? "success" : "idle"}`}>
          <Activity size={13} /> {found ? "Route found" : "Awaiting run"}
        </span>
      </div>

      <div className="metric-grid">
        <MetricCard icon={<Route size={17} />} label="Khoảng cách" value={formatDistance(metrics?.total_distance_m)} tone="#38bdf8" />
        <MetricCard icon={<Clock3 size={17} />} label="ETA mô phỏng" value={formatTime(metrics?.total_time_min)} tone="#34d399" />
        <MetricCard icon={<Gauge size={17} />} label="Tổng cost" value={compactNumber(metrics?.total_cost)} tone="#fbbf24" />
        <MetricCard icon={<Cpu size={17} />} label="Search time" value={formatRuntime(metrics?.processing_time_ms)} tone="#c084fc" />
        <MetricCard icon={<Brain size={17} />} label="Nút đã mở rộng" value={compactNumber(metrics?.explored_nodes)} tone="#22d3ee" />
        <MetricCard icon={<Milestone size={17} />} label="Frontier peak" value={compactNumber(metrics?.frontier_peak)} tone="#fb7185" />
      </div>

      <div className="route-strip">
        <div className="subheading-row"><span><Milestone size={15} /> Tuyến / thứ tự ghé</span><small>{metrics?.hop_count ?? Math.max(pathNames.length - 1, 0)} chặng</small></div>
        {pathNames.length ? (
          <div className="path-scroll">
            {pathNames.map((name, index) => (
              <span key={`${name}-${index}`}><i>{index + 1}</i>{name}</span>
            ))}
          </div>
        ) : <div className="empty-route">Tuyến tối ưu sẽ được vẽ và liệt kê sau khi chạy.</div>}
      </div>

      <div className="explanation-card">
        <div className="explanation-title"><Sparkles size={16} /> Vì sao chọn tuyến này?</div>
        <p>{explanation.summary}</p>
        {explanation.reasons.length > 0 && (
          <ul>{explanation.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul>
        )}
        {explanation.optimality && <div className="optimality-line"><ShieldCheck size={15} /> {explanation.optimality}</div>}
        {explanation.warnings.map((warning, index) => (
          <div className="warning-line" key={index}><AlertTriangle size={14} /> {warning}</div>
        ))}
      </div>

      {breakdown && (
        <div className="breakdown-card">
          <div className="subheading-row"><span><TrafficCone size={15} /> Cost breakdown</span><small>đã chuẩn hóa</small></div>
          <div className="breakdown-bars">
            {Object.entries(breakdown).filter(([key, value]) => key !== "total" && typeof value === "number").map(([key, value], index) => {
              const colors = ["#38bdf8", "#34d399", "#fbbf24", "#fb7185"];
              const total = breakdown.total || Object.values(breakdown).reduce<number>((sum, entry) => sum + (typeof entry === "number" ? entry : 0), 0) || 1;
              const width = Math.min(100, Math.max(3, ((value || 0) / total) * 100));
              return (
                <div className="breakdown-row" key={key}>
                  <span>{key.replaceAll("_", " ")}</span>
                  <div><i style={{ width: `${width}%`, background: colors[index % colors.length] }} /></div>
                  <b>{compactNumber(value)}</b>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {alternative && (
        <div className="alternative-card">
          <div className="subheading-row"><span><Activity size={15} /> Tuyến đối chứng</span><small>{alternative.label || "baseline"}</small></div>
          <p>{alternative.explanation || "Một lựa chọn hợp lệ khác để đối chiếu ảnh hưởng của cost và traffic."}</p>
          <div className="alternative-metrics">
            <span>{formatDistance(alternative.metrics?.total_distance_m)}</span>
            <span>{formatTime(alternative.metrics?.total_time_min)}</span>
            <span>cost {compactNumber(alternative.metrics?.total_cost)}</span>
          </div>
        </div>
      )}
    </aside>
  );
}
