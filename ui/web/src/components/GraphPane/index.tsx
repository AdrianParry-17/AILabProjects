import { MapPane } from "../MapPane";
import { RendererToggle } from "../RendererToggle";
import { useStore } from "../../state/store";
import styles from "./index.module.css";

/**
 * GraphPane (UI_IMPLEMENTATION_PLAN §7 T04/T08, MAP_RENDERING_SPEC §2/§10):
 * visualization host. Renders the segmented RendererToggle above the active
 * renderer. Switching the renderer is a pure frontend state change
 * (`setRenderer`) and never resets playback, search, or selection. The Map
 * branch is the default per spec; in P2 it mounts the same `MapPane` host
 * until the Leaflet canvas lands in P3 (T11).
 */
export function GraphPane(): JSX.Element {
  const renderer = useStore((s) => s.renderer);

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
