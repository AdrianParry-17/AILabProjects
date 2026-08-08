import { type CSSProperties, type ReactNode } from "react";

import styles from "./Tooltip.module.css";

export interface TooltipLine {
  label: string;
  value: string;
}

interface TooltipProps {
  /** Primary title (location/name). */
  title: string;
  /** Optional structured detail rows (id, type, coords, distance). */
  lines?: readonly TooltipLine[];
  /** Host content the tooltip annotates (hover source); optional for
   *  free-floating overlays rendered with `open`. */
  children?: ReactNode;
  /** Optional override classes for the host element. */
  className?: string;
  /** Inline positioning for the host (used by MapView for free positioning). */
  style?: CSSProperties;
  /** Render the tooltip as an always-visible overlay rather than hover-only. */
  open?: boolean;
}

/**
 * Shared tooltip (UI_TASK_BREAKDOWN §7 T13, MAP_RENDERING_SPEC §16,
 * MOTION_SPEC §17). Pure presentational; consumes only design tokens.
 *
 * Default behaviour: a CSS-driven hover/focus overlay (100 ms fade + 2 px
 * translateY) anchored above the host. Pass `open` to render persistently
 * (MapView popup overlay uses this); `prefers-reduced-motion` disables the
 * transition.
 */
export function Tooltip({
  title,
  lines,
  children,
  className,
  style,
  open,
}: TooltipProps): JSX.Element {
  const hostClass = [styles.host, className].filter(Boolean).join(" ");
  return (
    <span className={hostClass} style={style} role="tooltip" aria-label={title}>
      {children}
      <span
        className={styles.tooltip}
        data-open={open ? "true" : undefined}
        aria-hidden={open ? "false" : "true"}
      >
        <span className={styles.title}>{title}</span>
        {lines && lines.length > 0 ? (
          <span className={styles.lines}>
            {lines.map((line) => (
              <span key={line.label} className={styles.line}>
                <span className={styles.lineLabel}>{line.label}</span>
                <span className={styles.lineValue}>{line.value}</span>
              </span>
            ))}
          </span>
        ) : null}
      </span>
    </span>
  );
}
