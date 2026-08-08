import { useStore } from "../../../state/store";
import styles from "./index.module.css";

function PlayIcon(): JSX.Element {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M8 5v14l11-7L8 5Z" />
    </svg>
  );
}

function PauseIcon(): JSX.Element {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M6 5h4v14H6zM14 5h4v14h-4z" />
    </svg>
  );
}

function StepBackIcon(): JSX.Element {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M6 6h2v12H6zM18 6v12l-8-6 8-6Z" />
    </svg>
  );
}

function StepForwardIcon(): JSX.Element {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M16 6h2v12h-2zM6 18V6l8 6-8 6Z" />
    </svg>
  );
}

function RestartIcon(): JSX.Element {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="M4 10a8 8 0 1 1 2 4.6" strokeLinecap="round" />
      <path d="M4 5v5h5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** Playback control cluster (§2.8 / D.10): play/pause, step-back, step-forward, restart. */
export function AnimationControls(): JSX.Element {
  const status = useStore((s) => s.status);
  const playing = useStore((s) => s.playing);
  const activeIndex = useStore((s) => s.activeIndex);
  const last = useStore((s) => (s.result?.steps.length ?? 0) - 1);
  const play = useStore((s) => s.play);
  const pause = useStore((s) => s.pause);
  const stepTo = useStore((s) => s.stepTo);
  const restart = useStore((s) => s.restart);

  const canScrub =
    status === "Ready" || status === "Paused" || status === "Finished" || status === "Replay";
  const playDisabled =
    !playing && status !== "Ready" && status !== "Paused" && status !== "Replay";
  const stepBackDisabled = !canScrub || activeIndex <= 0;
  const stepForwardDisabled = !canScrub || activeIndex >= last || last < 0;
  const restartDisabled = status === "Idle" || status === "Loading" || status === "Error";

  return (
    <div className={styles.cluster}>
      <button
        type="button"
        className={`${styles.btn}${playing ? ` ${styles.active}` : ""}`}
        aria-label={playing ? "Pause" : "Play"}
        aria-pressed={playing}
        disabled={playDisabled}
        onClick={() => (playing ? pause() : play())}
      >
        {playing ? <PauseIcon /> : <PlayIcon />}
      </button>
      <button
        type="button"
        className={styles.btn}
        aria-label="Step back"
        disabled={stepBackDisabled}
        onClick={() => stepTo(activeIndex - 1)}
      >
        <StepBackIcon />
      </button>
      <button
        type="button"
        className={styles.btn}
        aria-label="Step forward"
        disabled={stepForwardDisabled}
        onClick={() => stepTo(activeIndex + 1)}
      >
        <StepForwardIcon />
      </button>
      <button
        type="button"
        className={styles.btn}
        aria-label="Restart"
        disabled={restartDisabled}
        onClick={restart}
      >
        <RestartIcon />
      </button>
    </div>
  );
}