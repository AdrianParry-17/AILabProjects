import styles from "./Spinner.module.css";

/** Shared spinner (IMPLEMENTATION_PLAN.md §D.10); respects reduced-motion. */
export function Spinner(): JSX.Element {
  return (
    <div className={styles.wrap} role="status" aria-label="Loading">
      <span className={styles.spinner} aria-hidden="true" />
    </div>
  );
}