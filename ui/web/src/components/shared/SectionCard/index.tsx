import type { ReactNode } from "react";

import styles from "./index.module.css";

interface SectionCardProps {
  title?: string;
  children: ReactNode;
}

/** Sidebar section card (COMPONENT_POLISH_SPEC §5); never transparent. */
export function SectionCard({ title, children }: SectionCardProps): JSX.Element {
  return (
    <section className={styles.card}>
      {title ? (
        <>
          <h2 className={styles.title}>{title}</h2>
          <div className={styles.divider} role="separator" aria-orientation="horizontal" />
        </>
      ) : null}
      <div className={styles.content}>{children}</div>
    </section>
  );
}