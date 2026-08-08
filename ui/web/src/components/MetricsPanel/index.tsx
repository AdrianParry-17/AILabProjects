import { useMemo, useState } from "react";

import { selectMetrics } from "../../lib/metrics";
import { useStore } from "../../state/store";
import { EmptyState } from "../shared/EmptyState";
import styles from "./index.module.css";

/**
 * MetricsPanel (§2.5 / D.6): the numeric outcome of the last search. Reads
 * `search.result`; derives rows via `selectMetrics` (tab numbers). The copy
 * button lazy-imports the export helper (§F.2).
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
        <h3 className={styles.title}>Metrics</h3>
        <EmptyState title="Run a search to see metrics" />
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
      <dl className={`${styles.list}${busy ? ` ${styles.dim}` : ""}`}>
        {rows.map((row) => (
          <div key={row.key} className={styles.row}>
            <dt className={styles.label}>{row.label}</dt>
            <dd className={styles.value}>{row.value}</dd>
          </div>
        ))}
      </dl>
      <p className={styles.explanation}>{result.explanation}</p>
    </section>
  );
}