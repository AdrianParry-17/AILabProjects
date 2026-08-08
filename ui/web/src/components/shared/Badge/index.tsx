import styles from "./index.module.css";

export type BadgeVariant = "info" | "success" | "warning" | "danger";

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
}

/** Small status badge (COMPONENT_POLISH_SPEC §20); fully rounded. */
export function Badge({ variant = "info", children }: BadgeProps): JSX.Element {
  return (
    <span className={[styles.badge, styles[variant]].join(" ")}>
      {children}
    </span>
  );
}