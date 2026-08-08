import styles from "./index.module.css";

interface SpeedSelectorProps {
  options: readonly number[];
  value: number;
  disabled?: boolean;
  onChange: (speed: number) => void;
}

/** Compact segmented speed selector (T16, MOTION_SPEC §12). Each option is a
 *  real <button> with `aria-pressed` so it behaves like a toggle group; the
 *  group itself is labelled for screen readers. No timers or animation here —
 *  the playback cadence is owned by `usePlayback`. */
export function SpeedSelector({
  options,
  value,
  disabled = false,
  onChange,
}: SpeedSelectorProps): JSX.Element {
  return (
    <div
      role="group"
      aria-label="Playback speed"
      className={`${styles.cluster}${disabled ? ` ${styles.disabled}` : ""}`}
    >
      {options.map((option) => (
        <button
          key={option}
          type="button"
          className={styles.btn}
          aria-pressed={option === value}
          aria-label={`${option}× speed`}
          disabled={disabled}
          onClick={() => onChange(option)}
        >
          {option}×
        </button>
      ))}
    </div>
  );
}
