import type { SearchResponse } from "../types";

export function formatDistance(value?: number): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value >= 1000 ? `${(value / 1000).toFixed(2)} km` : `${Math.round(value)} m`;
}

export function formatTime(value?: number): string {
  if (value == null || Number.isNaN(value)) return "—";
  if (value >= 60) return `${Math.floor(value / 60)}h ${Math.round(value % 60)}m`;
  return `${value.toFixed(value < 10 ? 1 : 0)} phút`;
}

export function formatRuntime(value?: number): string {
  if (value == null || Number.isNaN(value)) return "—";
  if (value < 1) return `${(value * 1000).toFixed(0)} μs`;
  return `${value.toFixed(value < 10 ? 2 : 1)} ms`;
}

export function compactNumber(value?: number): string {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(value);
}

const NODE_KIND_LABELS: Record<string, string> = {
  hospital: "Bệnh viện",
  supermarket: "Siêu thị",
  university: "Trường đại học",
  market: "Chợ",
  bus_station: "Bến xe buýt",
  bridge: "Cầu",
  gateway: "Nút kết nối",
  intersection: "Giao lộ",
};

export function formatNodeKind(value?: string): string {
  if (!value) return "Điểm giao nhận";
  const normalized = value.replace(/^delivery_/, "");
  return NODE_KIND_LABELS[normalized] || normalized.replaceAll("_", " ");
}

const COST_COMPONENT_LABELS: Record<string, string> = {
  distance: "Khoảng cách",
  distance_cost: "Khoảng cách",
  time: "Thời gian",
  time_cost: "Thời gian",
  travel_time: "Thời gian",
  congestion: "Ùn tắc",
  congestion_cost: "Ùn tắc",
  risk: "Rủi ro",
  risk_cost: "Rủi ro",
};

export function formatCostComponent(value: string): string {
  return COST_COMPONENT_LABELS[value] || value.replaceAll("_", " ");
}

export function explanationParts(explanation: SearchResponse["explanation"] | undefined) {
  if (!explanation) return { summary: "Chưa có kết quả để giải thích.", reasons: [], warnings: [] };
  if (typeof explanation === "string") return { summary: explanation, reasons: [], warnings: [] };
  return {
    summary: explanation.summary || "Tuyến đã được phân tích theo hàm chi phí đã chọn.",
    reasons: explanation.reasons || [],
    warnings: explanation.warnings || [],
    optimality: explanation.optimality,
  };
}

export function congestionColor(level: number, closed = false): string {
  if (closed) return "#ef4444";
  if (level >= 4.4) return "#f43f5e";
  if (level >= 3.4) return "#fb923c";
  if (level >= 2.4) return "#facc15";
  return "#34d399";
}

export const DEFAULT_WEIGHTS = {
  distance: 0.25,
  time: 0.5,
  congestion: 0.2,
  risk: 0.05,
};
