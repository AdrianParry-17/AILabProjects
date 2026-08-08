import type { CSSProperties } from "react";

import { useStore } from "../../state/store";
import { AnimationControls } from "../shared/AnimationControls";
import type { Step } from "../../services/animation";
import styles from "./index.module.css";
import { usePlayback } from "./usePlayback";

const EMPTY_STEPS: readonly Step[] = [];

/**
 * StepTimeline (UI_IMPLEMENTATION_PLAN.md §7 T07): scrubbable slider + playback
 * controls. Mounted in the bottom dock slot (`App.tsx`) which is full-width and
 * 96–120 px tall (LAYOUT_SPEC §16). Hides gracefully when no result exists.
 * Layout: counter + reason on the left, slider expanding to fill, playback
 * cluster on the right.
 */
export function StepTimeline(): JSX.Element | null {
  usePlayback();

  const steps = useStore((s) => s.result?.steps ?? EMPTY_STEPS);
  const activeIndex = useStore((s) => s.activeIndex);
  const status = useStore((s) => s.status);
  const stepTo = useStore((s) => s.stepTo);

  if (steps.length === 0) return null;

  const last = steps.length - 1;
  const index = activeIndex < 0 ? 0 : activeIndex;
  const reason = steps[index]?.reason ?? "";
  const disabled = status === "Idle" || status === "Error";
  const fill = `${last > 0 ? (index / last) * 100 : 0}%`;

  return (
    <section className={styles.wrap} aria-label="Search progress" data-testid="step-timeline">
      <div className={styles.meta}>
        <span className={styles.title}>Progress</span>
        <span className={styles.counter}>
          {index + 1} / {steps.length}
        </span>
        <span className={styles.reason} title={reason}>
          {reason}
        </span>
      </div>
      <input
        type="range"
        className={styles.slider}
        min={0}
        max={last}
        step={1}
        value={index}
        disabled={disabled}
        aria-label="Search step"
        aria-valuetext={`Step ${index + 1} of ${steps.length}`}
        style={{ "--fill": fill } as CSSProperties}
        onChange={(e) => stepTo(Number(e.target.value))}
      />
      <AnimationControls />
    </section>
  );
}