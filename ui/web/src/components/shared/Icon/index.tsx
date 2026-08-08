import type { LucideIcon } from "lucide-react";

import styles from "./index.module.css";

export type IconSize = "sm" | "md" | "lg" | "xl";

interface IconProps {
  icon: LucideIcon;
  size?: IconSize;
  label?: string;
}

/** Icon wrapper (UI_IMPLEMENTATION_PLAN.md §7 T02). Renders Lucide only. */
export function Icon({ icon: IconComponent, size = "md", label }: IconProps): JSX.Element {
  const aria = label
    ? { role: "img", "aria-label": label }
    : { "aria-hidden": true } as const;

  return (
    <span className={[styles.icon, styles[size]].join(" ")} {...aria}>
      <IconComponent />
    </span>
  );
}