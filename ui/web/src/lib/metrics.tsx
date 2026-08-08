import type { ReactNode } from "react";

import type { SearchResult } from "../api/types";
import { formatCost, formatDistanceKm, formatMilliseconds, formatMinutes } from "./format";

/** One rendered metric row: key, label, already-formatted value, and an
 *  optional leading icon (T15 — compact card layout). */
export interface MetricRow {
  key: string;
  label: string;
  value: string;
  icon?: ReactNode;
}

/** Icons are deliberately lightweight inline SVGs — kept here so the metrics
 *  library owns its presentation hints without leaking them into the panel. */
function DistanceIcon(): ReactNode {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 22s7-7 7-12a7 7 0 1 0-14 0c0 5 7 12 7 12Z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  );
}
function TimeIcon(): ReactNode {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}
function CostIcon(): ReactNode {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 2v20" />
      <path d="M17 6H9.5a3 3 0 0 0 0 6H14a3 3 0 0 1 0 6H6" />
    </svg>
  );
}
function NodesIcon(): ReactNode {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="6" cy="6" r="2.5" />
      <circle cx="18" cy="18" r="2.5" />
      <circle cx="18" cy="6" r="2.5" />
      <path d="M8 7.5 16 16.5" />
    </svg>
  );
}
function StepsIcon(): ReactNode {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 18h4v-4h4v-4h4V6h4" />
    </svg>
  );
}
function ClockIcon(): ReactNode {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 13a7 7 0 0 1 14 0" />
      <path d="M12 13l3-3" />
      <path d="M12 21a3 3 0 1 1 0-6 3 3 0 0 1 0 6Z" />
    </svg>
  );
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
    { key: "distance_km", label: "Distance", value: formatDistanceKm(result.total_distance_km), icon: <DistanceIcon /> },
    { key: "time_min", label: "Estimated Time", value: formatMinutes(result.total_time_min), icon: <TimeIcon /> },
    { key: "cost", label: "Cost", value: formatCost(result.total_cost), icon: <CostIcon /> },
    { key: "nodes_visited", label: "Nodes Visited", value: String(result.visited_nodes.length), icon: <NodesIcon /> },
    { key: "hops", label: "Steps", value: String(hops), icon: <StepsIcon /> },
    {
      key: "processing_time_ms",
      label: "Processing Time",
      value: formatMilliseconds(result.processing_time_ms),
      icon: <ClockIcon />,
    },
  ];
}