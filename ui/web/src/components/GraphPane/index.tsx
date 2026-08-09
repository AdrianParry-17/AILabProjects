import { MapPane } from "../MapPane";
import { RendererToggle } from "../RendererToggle";
import { Button } from "../shared/Button";
import { EmptyState } from "../shared/EmptyState";
import { useStore } from "../../state/store";
import styles from "./index.module.css";

/**
 * GraphPane (UI_IMPLEMENTATION_PLAN §7 T04/T08, MAP_RENDERING_SPEC §2/§10):
 * visualization host. Renders the segmented RendererToggle above the active
 * renderer. Switching the renderer is a pure frontend state change
 * (`setRenderer`) and never resets playback, search, or selection.
 *
 * T22 (UI_TASK_BREAKDOWN §7 T22): the region owns its loading / empty / error
 * surface so both renderers (Graph + Map) inherit the same behavior. Only the
 * post-graph tile-error path stays inside MapView (Retry tiles re-issues tile
 * requests and never calls the backend).
 */
export function GraphPane(): JSX.Element {
  const renderer = useStore((s) => s.renderer);
  const status = useStore((s) => s.status);
  const error = useStore((s) => s.error);
  const graph = useStore((s) => s.graph);
  const loadGraph = useStore((s) => s.loadGraph);

  // Loading skeleton — graph hasn't arrived yet.
  if (status === "Loading" && !graph) {
    return (
      <section className={styles.pane} role="region" aria-label="Visualization" data-testid="graph-pane">
        <div className={styles.toolbar}>
          <RendererToggle />
        </div>
        <div
          className={`${styles.stage} ${styles.skeletonStage}`}
          data-renderer={renderer}
          data-testid="graph-stage"
          data-graph-status="loading"
          aria-busy="true"
        />
      </section>
    );
  }

  // No graph yet: either a clean empty state ("Load graph to begin.") or the
  // graph-load failure surface (Retry → loadGraph). Per T22, the Retry button
  // is the only retry surface for this region.
  if (!graph) {
    const isError = status === "Error";
    return (
      <section className={styles.pane} role="region" aria-label="Visualization" data-testid="graph-pane">
        <div className={styles.toolbar}>
          <RendererToggle />
        </div>
        <div
          className={`${styles.stage} ${styles.overlayStage}`}
          data-renderer={renderer}
          data-testid="graph-stage"
          data-graph-status={isError ? "error" : "empty"}
        >
          <EmptyState
            title={isError ? "Graph load failed" : "Load graph to begin."}
            subtitle={isError ? error ?? "Could not load graph data." : undefined}
            icon={isError ? <ErrorIcon /> : undefined}
            action={
              isError ? (
                <Button onClick={() => void loadGraph()}>Retry</Button>
              ) : (
                <Button onClick={() => void loadGraph()}>Load graph</Button>
              )
            }
          />
        </div>
      </section>
    );
  }

  return (
    <section className={styles.pane} role="region" aria-label="Visualization" data-testid="graph-pane">
      <div className={styles.toolbar}>
        <RendererToggle />
      </div>
      <div className={styles.stage} data-renderer={renderer} data-testid="graph-stage">
        <MapPane />
      </div>
    </section>
  );
}

/** Decorative error glyph for the visualization empty/error state. */
function ErrorIcon(): JSX.Element {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}
