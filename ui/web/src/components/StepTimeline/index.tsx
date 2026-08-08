import type { CSSProperties } from "react";

import { useStore } from "../../state/store";
import { AnimationControls } from "../shared/AnimationControls";
import { SpeedSelector } from "../shared/SpeedSelector";
import type { Step } from "../../services/animation";
import styles from "./index.module.css";
import { usePlayback } from "./usePlayback";

const EMPTY_STEPS: readonly Step[] = [];

const SPEED_OPTIONS: readonly number[] = [0.5, 1, 2, 4];

/**
 * StepTimeline (UI_IMPLEMENTATION_PLAN §7 T07/T16, COMPONENT_POLISH_SPEC §13,
 * MOTION_SPEC §12). Scrubbable slider + playback controls + speed selector.
 * Mounted in the bottom dock slot (`App.tsx`), full-width and 96–120 px tall
 * (LAYOUT_SPEC §16). Hides gracefully when no result exists.
 *
 * Layout: meta row (counter + reason) — slider expanding to fill — speed
 * selector — playback cluster. The slider uses CSS custom property `--fill`
 * so the active progress is painted in token colours without JS animation.
 */
export function StepTimeline(): JSX.Element | null {
  usePlayback();

  const steps = useStore((s) => s.result?.steps ?? EMPTY_STEPS);
  const activeIndex = useStore((s) => s.activeIndex);
  const status = useStore((s) => s.status);
  const speed = useStore((s) => s.speed);
  const stepTo = useStore((s) => s.stepTo);
  const setSpeed = useStore((s) => s.setSpeed);

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
      <SpeedSelector
        options={SPEED_OPTIONS}
        value={speed}
        disabled={disabled}
        onChange={setSpeed}
      />
      <AnimationControls />
    </section>
  );
}