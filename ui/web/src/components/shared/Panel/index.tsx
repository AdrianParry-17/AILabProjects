import type { ReactNode } from "react";

import styles from "./index.module.css";

interface PanelProps {
  title?: string;
  icon?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
}

/** Reusable surface container (UI_IMPLEMENTATION_PLAN.md §7 T02). */
export function Panel({ title, icon, footer, children }: PanelProps): JSX.Element {
  return (
    <section className={styles.panel}>
      {title ? (
        <header className={styles.header}>
          {icon ? <span className={styles.icon}>{icon}</span> : null}
          <h2 className={styles.title}>{title}</h2>
        </header>
      ) : null}
      <div className={styles.body}>{children}</div>
      {footer ? <footer className={styles.footer}>{footer}</footer> : null}
    </section>
  );
}