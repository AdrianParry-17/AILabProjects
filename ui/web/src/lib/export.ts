import type { MetricRow } from "./metrics";

/**
 * Copy the metrics to the clipboard as plain text. Kept in its own module so
 * the MetricsPanel can import it lazily (IMPLEMENTATION_PLAN.md §F.2/F.3 —
 * "MetricsPanel-export" chunk), keeping the core bundle small.
 */
export async function copyMetricsText(
  rows: readonly MetricRow[],
  explanation?: string,
): Promise<void> {
  const lines = rows.map((row) => `${row.label}: ${row.value}`);
  if (explanation) lines.push(`\n${explanation}`);
  if (!navigator.clipboard?.writeText) {
    throw new Error("Clipboard not available.");
  }
  await navigator.clipboard.writeText(lines.join("\n"));
}