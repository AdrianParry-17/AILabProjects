import { useMemo, useState } from "react";

import { selectMetrics } from "../../lib/metrics";
import { useStore } from "../../state/store";
import { EmptyState } from "../shared/EmptyState";
import styles from "./index.module.css";

/**
 * MetricsPanel (UI_TASK_BREAKDOWN §7 T15, UI_POLISH_SPEC §13,
 * COMPONENT_POLISH_SPEC §11, LAYOUT_SPEC §21): compact uniform cards, not a
 * table. Each card = icon + title + value (value contains its unit per the
 * existing `lib/format` helpers — see `formatDistanceKm`/`formatMinutes`).
 * 2-column grid on desktop via T01 card tokens (padding/radius/gap/border/
 * bg/elevation). Empty state reuses the shared `EmptyState`.
 */
export function MetricsPanel(): JSX.Element {
  const result = useStore((s) => s.result);
  const busy = useStore((s) => s.busy);
  const [copied, setCopied] = useState(false);

  const rows = useMemo(() => selectMetrics(result), [result]);

  async function onCopy(): Promise<void> {
    try {
      const { copyMetricsText } = await import("../../lib/export");
      await copyMetricsText(rows, result?.explanation);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  if (!result) {
    return (
      <section className={styles.wrap}>
        <div className={styles.titleRow}>
          <h3 className={styles.title}>Metrics</h3>
        </div>
        <EmptyState
          title="Run a search to see metrics"
          subtitle="Choose a start location and a destination, then click Run Search."
        />
      </section>
    );
  }

  return (
    <section className={styles.wrap} aria-label="Result metrics">
      <div className={styles.titleRow}>
        <h3 className={styles.title}>Metrics</h3>
        <button type="button" className={styles.copy} onClick={() => void onCopy()}>
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <ul className={`${styles.grid}${busy ? ` ${styles.dim}` : ""}`}>
        {rows.map((row) => (
          <li key={row.key} className={styles.card}>
            <span className={styles.icon}>{row.icon}</span>
            <span className={styles.cardLabel}>{row.label}</span>
            <span className={styles.cardValue}>{row.value}</span>
          </li>
        ))}
      </ul>
      <p className={styles.explanation}>{result.explanation}</p>
    </section>
  );
}