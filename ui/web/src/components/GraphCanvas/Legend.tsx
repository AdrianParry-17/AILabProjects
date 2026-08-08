/**
 * Legend (UI_IMPLEMENTATION_PLAN §7 T09, COMPONENT_POLISH §3.4): colour key for
 * the GraphCanvas overlay. Lists every node + edge state that the canvas
 * paints, in the same order as the layer stack so the legend always reads
 * top-to-bottom matching top-to-bottom rendering.
 */
import styles from "./index.module.css";

export function Legend(): JSX.Element {
  return (
    <ul className={styles.legend} role="note" aria-label="Map legend">
      <li className={styles.legendItem}>
        <span className={`${styles.legendSwatch} ${styles.legendSwatchStart}`} aria-hidden="true" />
        start
      </li>
      <li className={styles.legendItem}>
        <span className={`${styles.legendSwatch} ${styles.legendSwatchGoal}`} aria-hidden="true" />
        goal
      </li>
      <li className={styles.legendItem}>
        <span className={`${styles.legendSwatch} ${styles.legendSwatchCurrent}`} aria-hidden="true" />
        current
      </li>
      <li className={styles.legendItem}>
        <span className={`${styles.legendSwatch} ${styles.legendSwatchFrontier}`} aria-hidden="true" />
        frontier
      </li>
      <li className={styles.legendItem}>
        <span className={`${styles.legendSwatch} ${styles.legendSwatchVisited}`} aria-hidden="true" />
        visited
      </li>
      <li className={styles.legendItem}>
        <span className={`${styles.legendSwatch} ${styles.legendSwatchRoute}`} aria-hidden="true" />
        route
      </li>
    </ul>
  );
}
