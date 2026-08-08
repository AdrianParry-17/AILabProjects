import type { SearchResult } from "../api/types";
import { formatCost, formatDistanceKm, formatMilliseconds, formatMinutes } from "./format";

/** One rendered metric row: key, label and already-formatted value. */
export interface MetricRow {
  key: string;
  label: string;
  value: string;
}

/**
 * Derive the metric rows from a `SearchResult` (COMPONENT_SPEC §0.2). The four
 * headline numbers are copied verbatim from the result; `hops` and
 * `nodes_visited` are front-end derived. Returns [] when there is no result.
 */
export function selectMetrics(result: SearchResult | null): MetricRow[] {
  if (!result) return [];
  const hops = result.path.length > 0 ? result.path.length - 1 : 0;
  return [
    { key: "distance_km", label: "Distance", value: formatDistanceKm(result.total_distance_km) },
    { key: "time_min", label: "Estimated Time", value: formatMinutes(result.total_time_min) },
    { key: "cost", label: "Cost", value: formatCost(result.total_cost) },
    { key: "nodes_visited", label: "Nodes Visited", value: String(result.visited_nodes.length) },
    { key: "hops", label: "Steps", value: String(hops) },
    {
      key: "processing_time_ms",
      label: "Processing Time",
      value: formatMilliseconds(result.processing_time_ms),
    },
  ];
}