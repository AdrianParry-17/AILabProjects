import { GraphCanvas } from "../GraphCanvas";
import { MapView } from "../MapView";
import { useStore } from "../../state/store";
import styles from "./index.module.css";

/**
 * MapPane (UI_IMPLEMENTATION_PLAN §7 T08/T11). Full-bleed canvas container.
 * Renders the store-driven `renderer` state: the Leaflet MapView (default per
 * MAP_RENDERING_SPEC §2) or the SVG GraphCanvas. The pane owns layout only;
 * both renderers read the store directly, consuming the same derived Frame.
 */
export function MapPane(): JSX.Element {
  const renderer = useStore((s) => s.renderer);

  return (
    <div className={styles.pane} data-testid="map-pane" data-renderer={renderer}>
      {renderer === "graph" ? <GraphCanvas /> : <MapView />}
    </div>
  );
}