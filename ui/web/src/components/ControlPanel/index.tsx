import { useMemo } from "react";

import { useStore } from "../../state/store";
import { SectionCard } from "../shared/SectionCard";
import { AlgorithmSelector } from "../AlgorithmSelector";
import { NodePicker, type NodeOption } from "../shared/NodePicker";
import styles from "./index.module.css";

/**
 * ControlPanel (UI_IMPLEMENTATION_PLAN.md §7 T05, COMPONENT_POLISH_SPEC §4):
 * search configuration grouped into three ordered SectionCards — Search
 * (start + goal), Algorithm (selector), Execution (Run). The form wraps all
 * three so Enter submits from any input. Store-driven; writes via store
 * actions only. No store/API/state-machine changes.
 */
export function ControlPanel(): JSX.Element {
  const graph = useStore((s) => s.graph);
  const status = useStore((s) => s.status);
  const catalog = useStore((s) => s.catalog);
  const selectedAlgorithm = useStore((s) => s.selectedAlgorithm);
  const start = useStore((s) => s.start);
  const goal = useStore((s) => s.goal);
  const busy = useStore((s) => s.busy);
  const setAlgorithm = useStore((s) => s.setAlgorithm);
  const setStart = useStore((s) => s.setStart);
  const setGoal = useStore((s) => s.setGoal);
  const runSearch = useStore((s) => s.runSearch);

  const nodes: NodeOption[] = useMemo(
    () => (graph?.nodes ?? []).map((n) => ({ id: n.id, name: n.name || n.id })),
    [graph],
  );

  const graphLoaded = Boolean(graph);
  const editable = graphLoaded && (status === "Ready" || status === "Error");
  const bothChosen = Boolean(start && goal);
  const invalid = Boolean(start && goal && start === goal);
  const canRun = editable && !busy && Boolean(selectedAlgorithm) && bothChosen && !invalid;

  function submit(): void {
    if (canRun) void runSearch();
  }

  return (
    <form
      className={styles.panel}
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
      aria-label="Search configuration"
    >
      <fieldset disabled={!editable} className={styles.fieldset} aria-label="Search controls">
        <SectionCard title="Search">
          <NodePicker label="Start Location" value={start} options={nodes} disabled={!editable} onChange={setStart} />
          <NodePicker label="Destination" value={goal} options={nodes} disabled={!editable} onChange={setGoal} />
        </SectionCard>

        <SectionCard title="Algorithm">
          <AlgorithmSelector catalog={catalog} value={selectedAlgorithm} disabled={!editable} onChange={setAlgorithm} />
        </SectionCard>

        <SectionCard title="Execution">
          {!bothChosen && !invalid ? (
            <p className={styles.hint} role="status">
              Select a start location and a destination.
            </p>
          ) : null}
          {invalid ? (
            <p className={styles.invalid} role="alert">
              Start and destination must be different.
            </p>
          ) : null}
          <button type="submit" className={styles.run} disabled={!canRun}>
            {busy ? "Running…" : "Run Search"}
          </button>
        </SectionCard>
      </fieldset>
    </form>
  );
}