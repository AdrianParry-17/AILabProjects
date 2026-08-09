import { Suspense, lazy, useMemo } from "react";

import { useStore } from "../../state/store";
import { SectionCard } from "../shared/SectionCard";
import { MetricsPanel } from "../MetricsPanel";
import { StatusSection } from "./StatusSection";
import styles from "./index.module.css";

const HistoryPanel = lazy(() => import("../HistoryPanel"));

/**
 * InfoPanel (UI_IMPLEMENTATION_PLAN.md §7 T06, LAYOUT_SPEC §13, UI_POLISH_SPEC §12):
 * the right-hand information region. Composes four blocks from top to bottom:
 *   1. Status section (always visible — absorbs the deleted StatusBar).
 *   2. Metrics section (compact cards via `MetricsPanel`).
 *   3. Search explanation / current step / current frontier (carried in
 *      `MetricsPanel` already — its `explanation` text satisfies this).
 *   4. History panel (moved from the sidebar in T05; lazy-loaded chunk).
 * No search controls live here. Independent vertical scroll.
 */
export function InfoPanel(): JSX.Element {
  const history = useStore((s) => s.history);
  const historyLoading = useStore((s) => s.historyLoading);
  const historyError = useStore((s) => s.historyError);
  const replayRunId = useStore((s) => s.replayRunId);
  const status = useStore((s) => s.status);
  const replayRun = useStore((s) => s.replayRun);
  const catalog = useStore((s) => s.catalog);

  const labelFor = useMemo(() => {
    const byId = new Map(catalog.map((a) => [a.id, a.label]));
    return (algorithmId: string): string => byId.get(algorithmId) ?? algorithmId;
  }, [catalog]);

  const ready = status !== "Idle" && status !== "Loading";

  return (
    <div className={styles.panel} role="region" aria-label="Search information" data-testid="info-panel">
      <SectionCard title="Status">
        <StatusSection />
      </SectionCard>

      <MetricsPanel />

      <SectionCard title="History">
        {ready ? (
          <Suspense fallback={null}>
            <HistoryPanel
              history={history}
              activeRunId={replayRunId}
              loading={historyLoading}
              historyError={historyError}
              labelFor={labelFor}
              onReplay={replayRun}
            />
          </Suspense>
        ) : (
          <p className={styles.historyHint}>Run a search to record history.</p>
        )}
      </SectionCard>
    </div>
  );
}