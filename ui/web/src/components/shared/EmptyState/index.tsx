import type { ReactNode } from "react";

import styles from "./index.module.css";

interface EmptyStateProps {
  title: string;
  subtitle?: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
}

/** Shared empty-state placeholder (COMPONENT_POLISH_SPEC §21). */
export function EmptyState({ title, subtitle, description, icon, action }: EmptyStateProps): JSX.Element {
  const text = subtitle ?? description;
  return (
    <div className={styles.empty} role="status">
      {icon ? <div className={styles.illustration}>{icon}</div> : null}
      <p className={styles.title}>{title}</p>
      {text ? <p className={styles.subtitle}>{text}</p> : null}
      {action ? <div className={styles.action}>{action}</div> : null}
    </div>
  );
}