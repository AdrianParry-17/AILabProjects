import { useStore } from "../../state/store";
import styles from "./index.module.css";

/** Per-state display text — mirrors the deleted StatusBar mapping (COMPONENT_SPEC §2.10). */
const STATE_TEXT: Record<string, string> = {
  Idle: "Loading…",
  Loading: "Loading…",
  Ready: "Ready",
  Playing: "Playing",
  Paused: "Paused",
  Finished: "Finished",
  Error: "Error — retry",
  Replay: "Replay",
};

/**
 * StatusSection (UI_IMPLEMENTATION_PLAN.md §7 T06): absorbs the deleted
 * `StatusBar` responsibilities inside the InfoPanel Status section. Always
 * visible; shows the dot + state text, the `(mock)` marker, and a Retry
 * button when the graph itself failed to load.
 */
export function StatusSection(): JSX.Element {
  const status = useStore((s) => s.status);
  const source = useStore((s) => s.source);
  const error = useStore((s) => s.error);
  const searchError = useStore((s) => s.searchError);
  const graphReady = useStore((s) => Boolean(s.graph));
  const loadGraph = useStore((s) => s.loadGraph);

  const message =
    status === "Error" ? (searchError ?? error ?? STATE_TEXT[status]) : (STATE_TEXT[status] ?? status);
  const isMock = source === "mock";

  return (
    <div className={styles.row} data-testid="status-section" role="status" aria-live="polite">
      <span className={styles.dot} data-state={status} aria-hidden="true" />
      <span className={styles.text}>{message}</span>
      {isMock ? (
        <span className={styles.mock} aria-hidden="true">
          (mock)
        </span>
      ) : null}
      {status === "Error" && !graphReady ? (
        <button type="button" className={styles.retry} onClick={() => void loadGraph()}>
          Retry
        </button>
      ) : null}
    </div>
  );
}