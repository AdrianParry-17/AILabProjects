import { memo } from "react";
import { Award, BrainCircuit, Clock3, Cpu, Gauge, Network, Route } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CompareResponse, MetadataPayload } from "../types";
import { compactNumber, formatDistance, formatRuntime, formatTime } from "../lib/format";

export const ComparePanel = memo(function ComparePanel({ data, metadata }: { data?: CompareResponse; metadata: MetadataPayload }) {
  const rows = (data?.results || []).map((result) => ({
    id: result.algorithm,
    name: metadata.algorithms.find((item) => item.id === result.algorithm)?.name || result.algorithm,
    cost: result.found ? result.metrics.total_cost : null,
    distance: result.metrics.total_distance_m,
    time: result.metrics.total_time_min,
    explored: result.metrics.explored_nodes,
    runtime: result.metrics.processing_time_ms,
    frontier: result.metrics.frontier_peak || 0,
    found: result.found,
  }));
  const successfulRows = rows.filter((row) => row.found && row.cost != null);
  const backendWinner = data?.winner && successfulRows.some((row) => row.id === data.winner) ? data.winner : undefined;
  const winner = backendWinner || (successfulRows.length ? [...successfulRows].sort((a, b) => Number(a.cost) - Number(b.cost))[0].id : undefined);
  const colors = ["#38bdf8", "#34d399", "#fbbf24", "#c084fc", "#fb7185", "#22d3ee", "#a3e635", "#f97316"];

  return (
    <aside className="compare-panel panel">
      <div className="panel-heading compact">
        <div>
          <span className="section-kicker">CONTROLLED BENCHMARK</span>
          <h2>Algorithm arena</h2>
        </div>
        <span className="status-pill success"><Network size={13} /> cùng graph snapshot</span>
      </div>

      {!rows.length ? (
        <div className="compare-empty">
          <BrainCircuit size={38} />
          <h3>Chưa có benchmark</h3>
          <p>Chọn tối thiểu hai thuật toán. Tất cả sẽ chạy trên cùng graph, traffic scenario, objective và weights để so sánh công bằng.</p>
        </div>
      ) : (
        <>
          {winner && (
            <div className="winner-card">
              <Award size={24} />
              <div><small>Hiệu quả nhất theo total cost</small><strong>{rows.find((row) => row.id === winner)?.name || winner}</strong></div>
            </div>
          )}
          {!winner && (
            <div className="compare-empty compact">
              <BrainCircuit size={26} />
              <h3>Chưa thuật toán nào tìm thấy tuyến</h3>
              <p>Hãy đổi điểm giao nhận, kịch bản giao thông hoặc giới hạn tìm kiếm rồi chạy lại benchmark.</p>
            </div>
          )}

          <div className="chart-card">
            <div className="subheading-row"><span><Gauge size={15} /> Cost & search effort</span><small>lower is better</small></div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={rows} margin={{ top: 12, right: 4, bottom: 4, left: -18 }}>
                <CartesianGrid stroke="#203044" strokeDasharray="3 5" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: "#0b1727", border: "1px solid #294058", borderRadius: 10, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="cost" name="Total cost" radius={[5, 5, 0, 0]}>
                  {rows.map((row, index) => <Cell key={row.id} fill={colors[index % colors.length]} />)}
                </Bar>
                <Bar dataKey="explored" name="Explored" fill="#334155" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="benchmark-table-wrap">
            <table className="benchmark-table">
              <thead>
                <tr><th>Thuật toán</th><th><Route size={12} /> Tuyến</th><th><Clock3 size={12} /> ETA</th><th><Gauge size={12} /> Cost</th><th><BrainCircuit size={12} /> Expanded</th><th><Cpu size={12} /> Runtime</th></tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} className={row.id === winner ? "winner" : row.found ? "" : "failed"}>
                    <td><i style={{ background: colors[rows.indexOf(row) % colors.length] }} /> <strong>{row.name}</strong>{row.id === winner && <Award size={13} />}</td>
                    <td>{row.found ? formatDistance(row.distance) : "Không có tuyến"}</td>
                    <td>{row.found ? formatTime(row.time) : "—"}</td>
                    <td>{row.found ? compactNumber(row.cost ?? undefined) : "—"}</td>
                    <td>{row.explored}</td>
                    <td>{formatRuntime(row.runtime)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="benchmark-insight">
            <BrainCircuit size={17} />
            <p>{data?.insight || "Một cost bằng nhau không có nghĩa hành vi giống nhau: expansion order, frontier peak và runtime cho thấy chiến lược tìm kiếm khác biệt."}</p>
          </div>
        </>
      )}
    </aside>
  );
});
