/**
 * Number/label formatting helpers (IMPLEMENTATION_PLAN.md §A.3 tabular-nums,
 * §F.3 use Intl — no date/moment lib).
 */

/** Format a kilometre distance with 2 decimals, e.g. "3.20 km". */
export function formatDistanceKm(km: number): string {
  return `${km.toFixed(2)} km`;
}

/** Format a cost with 2 decimals. */
export function formatCost(cost: number): string {
  return cost.toFixed(2);
}

/** Format a duration estimate in minutes. */
export function formatMinutes(min: number): string {
  return `${min.toFixed(1)} min`;
}

/** Format a processing time in milliseconds. */
export function formatMilliseconds(ms: number): string {
  return `${ms.toFixed(1)} ms`;
}

/** Label for a POI kind (fallback to the raw kind string). */
export function kindLabel(kind: string): string {
  const labels: Record<string, string> = {
    delivery_market: "Market",
    delivery_supermarket: "Supermarket",
    delivery_warehouse: "Warehouse",
    delivery_bus_station: "Bus Station",
    delivery_hospital: "Hospital",
  };
  return labels[kind] ?? kind;
}

/**
 * Human relative time from an ISO timestamp, e.g. "3 minutes ago" (UI §9.6
 * HistoryPanel "time ago"; IMPLEMENTATION_PLAN §F.3 — Intl, no date/moment lib).
 */
export function formatTimeAgo(iso: string, now: number = Date.now()): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const seconds = Math.round((then - now) / 1000);
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  const abs = Math.abs(seconds);
  if (abs < 60) return rtf.format(Math.max(-59, Math.min(59, seconds)), "second");
  if (abs < 3600) return rtf.format(Math.round(seconds / 60), "minute");
  if (abs < 86400) return rtf.format(Math.round(seconds / 3600), "hour");
  if (abs < 604800) return rtf.format(Math.round(seconds / 86400), "day");
  if (abs < 2592000) return rtf.format(Math.round(seconds / 604800), "week");
  if (abs < 31536000) return rtf.format(Math.round(seconds / 2592000), "month");
  return rtf.format(Math.round(seconds / 31536000), "year");
}