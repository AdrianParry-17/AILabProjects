import { memo } from "react";

import { formatTimeAgo } from "../../lib/format";
import type { HistoryRun } from "../../api/types";
import { EmptyState } from "../shared/EmptyState";
import styles from "./index.module.css";

interface HistoryPanelProps {
  history: readonly HistoryRun[];
  activeRunId?: string | null;
  loading?: boolean;
  /** T22 inline error indicator (no retry — retry is reserved for the
   *  exhaustive list of retry-bearing errors). */
  historyError?: string | null;
  labelFor?: (algorithmId: string) => string;
  onReplay: (id: string) => void;
}

const identity = (id: string): string => id;

/**
 * One memoized history row: algorithm name, start→goal, time ago, source badge
 * (§2.6 / UI §9.6). The row is a replay button with an explicit aria-label.
 */
const HistoryRow = memo(function HistoryRow({
  run,
  active,
  labelFor,
  onReplay,
}: {
  run: HistoryRun;
  active: boolean;
  labelFor: (algorithmId: string) => string;
  onReplay: (id: string) => void;
}): JSX.Element {
  const label = labelFor(run.algorithm);
  return (
    <li>
      <button
        type="button"
        className={`${styles.row}${active ? ` ${styles.active}` : ""}`}
        aria-current={active ? "true" : undefined}
        aria-label={`Replay ${label} run from ${run.start} to ${run.goal}`}
        onClick={() => onReplay(run.id)}
      >
        <span className={styles.algo}>{label}</span>
        <span className={styles.route}>
          {run.start} → {run.goal}
        </span>
        <span className={styles.meta}>
          <span>{run.hops} hops</span>
          <span>{formatTimeAgo(run.created_at)}</span>
          {run.source === "mock" ? <span className={styles.badge}>mock</span> : null}
        </span>
      </button>
    </li>
  );
});

/**
 * HistoryPanel (§2.6 / D.7): lists past runs and replays from stored steps. The
 * run's full `result` is hydrated client-side by `replayRun(id)` — replay never
 * performs a network call. This file is lazy-loaded by `Sidebar` (§F lazy chunk).
 * While `loading` it renders a skeleton instead of the empty state.
 */
export function HistoryPanel({
  history,
  activeRunId = null,
  loading = false,
  historyError = null,
  labelFor = identity,
  onReplay,
}: HistoryPanelProps): JSX.Element {
  return (
    <section className={styles.wrap} aria-label="Search history">
      <h3 className={styles.title}>History</h3>
      {loading ? (
        <div className={styles.skeleton} role="status" aria-label="Loading history">
          <div className={styles.skeletonRow} />
          <div className={styles.skeletonRow} />
          <div className={styles.skeletonRow} />
        </div>
      ) : historyError ? (
        <p className={styles.error} role="status" data-testid="history-error">
          {historyError}
        </p>
      ) : history.length === 0 ? (
        <EmptyState title="No searches recorded yet." subtitle="Runs appear here after you search." />
      ) : (
        <ul className={styles.list}>
          {history.map((run) => (
            <HistoryRow key={run.id} run={run} active={run.id === activeRunId} labelFor={labelFor} onReplay={onReplay} />
          ))}
        </ul>
      )}
    </section>
  );
}

export default HistoryPanel;
