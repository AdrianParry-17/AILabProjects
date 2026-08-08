import { useStore } from "../../state/store";
import styles from "./index.module.css";

const OPTIONS: ReadonlyArray<{ id: "graph" | "map"; label: string }> = [
  { id: "graph", label: "Graph" },
  { id: "map", label: "Map" },
];

/**
 * RendererToggle (UI_IMPLEMENTATION_PLAN §7 T08, MAP_RENDERING_SPEC §2/§10):
 * segmented control that switches between the Graph and Map renderers. The
 * active renderer is sourced from the store; clicking a segment calls
 * `setRenderer`, which is a pure frontend state mutation (no backend calls).
 *
 * Accessibility:
 *   - `role="group"` + `aria-label` on the container
 *   - each option is a real `<button type="button">` with `aria-pressed`
 *   - keyboard reachable in DOM order (Tab / Shift+Tab)
 *   - focus ring via `--focus-ring`
 *   - reduced-motion respected (no transitions)
 *
 * P2 limitation: the Map branch in `GraphPane` mounts the same graph host
 * until the Leaflet canvas lands in P3 (T11). The toggle is therefore
 * observable (state + UI) but visually identical between modes for now; the
 * default is "map" per MAP_RENDERING_SPEC §2.
 */
export function RendererToggle(): JSX.Element {
  const renderer = useStore((s) => s.renderer);
  const setRenderer = useStore((s) => s.setRenderer);

  return (
    <div className={styles.group} role="group" aria-label="Visualization renderer">
      <span className={styles.label}>View</span>
      <div className={styles.segment}>
        {OPTIONS.map((opt) => {
          const active = renderer === opt.id;
          return (
            <button
              key={opt.id}
              type="button"
              className={styles.option}
              aria-pressed={active}
              aria-label={`${opt.label} view`}
              data-renderer={opt.id}
              onClick={() => {
                if (!active) setRenderer(opt.id);
              }}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
