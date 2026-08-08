import { ControlPanel } from "../ControlPanel";
import styles from "./index.module.css";

/**
 * Sidebar (UI_IMPLEMENTATION_PLAN.md §7 T05, COMPONENT_POLISH_SPEC §4): the
 * left control surface. Houses the search configuration grouped into
 * SectionCards by `ControlPanel`. Metrics and History were removed in T05
 * (they move to the right InfoPanel in T06); the playback timeline moves to
 * the bottom dock in T07. Below 1024 px the sidebar collapses to a drawer
 * anchored to the left edge with `--motion-normal` slide + `--ease-panel`
 * (LAYOUT_SPEC §19, MOTION_SPEC §15).
 */
export function Sidebar(): JSX.Element {
  return (
    <aside className={styles.sidebar} aria-label="Search controls">
      <ControlPanel />
    </aside>
  );
}