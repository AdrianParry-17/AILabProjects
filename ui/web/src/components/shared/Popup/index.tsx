import { useEffect, useRef } from "react";

import { kindLabel } from "../../../lib/format";
import { Button } from "../Button";
import styles from "./index.module.css";

export interface PopupNode {
  id: string;
  name: string;
  kind: string;
  latitude: number;
  longitude: number;
}

interface PopupProps {
  /** The node whose details are displayed. */
  node: PopupNode;
  /** "Set as Start" — must call the existing store `setStart` action. */
  onSetStart: (id: string) => void;
  /** "Set as Goal" — must call the existing store `setGoal` action. */
  onSetGoal: (id: string) => void;
  /** "Center Here" — map-side pan-to-anchor. */
  onCenter: () => void;
  /** "Close" — dismiss the popup. */
  onClose: () => void;
  /** Optional overlay positioning (MapView passes absolute coordinates). */
  style?: React.CSSProperties;
}

/**
 * Shared Popup (UI_TASK_BREAKDOWN §7 T13, MAP_RENDERING_SPEC §17). Rendered
 * ONLY by MapView (graph mode has no popup). Presentational; all actions
 * delegate to existing store actions — no backend/API behaviour here.
 * Keyboard: Escape closes; the action buttons are real `<button>`s.
 */
export function Popup({
  node,
  onSetStart,
  onSetGoal,
  onCenter,
  onClose,
  style,
}: PopupProps): JSX.Element {
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const onKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") onClose();
    };
    root.addEventListener("keydown", onKeyDown);
    const first = root.querySelector<HTMLButtonElement>("button");
    first?.focus();
    return () => root.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      ref={rootRef}
      role="dialog"
      aria-label={`${node.name} (${kindLabel(node.kind)})`}
      className={styles.popup}
      style={style}
      tabIndex={-1}
    >
      <div className={styles.header}>
        <span className={styles.title}>{node.name}</span>
        <button type="button" className={styles.close} onClick={onClose} aria-label="Close popup">
          ×
        </button>
      </div>
      <dl className={styles.meta}>
        <div className={styles.row}>
          <dt>Type</dt>
          <dd>{kindLabel(node.kind)}</dd>
        </div>
        <div className={styles.row}>
          <dt>Latitude</dt>
          <dd>{node.latitude.toFixed(5)}</dd>
        </div>
        <div className={styles.row}>
          <dt>Longitude</dt>
          <dd>{node.longitude.toFixed(5)}</dd>
        </div>
      </dl>
      <div className={styles.actions}>
        <Button variant="secondary" size="small" onClick={() => onSetStart(node.id)}>
          Set as Start
        </Button>
        <Button variant="secondary" size="small" onClick={() => onSetGoal(node.id)}>
          Set as Goal
        </Button>
        <Button variant="ghost" size="small" onClick={onCenter}>
          Center Here
        </Button>
      </div>
    </div>
  );
}