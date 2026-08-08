import { useEffect } from "react";

import { useStore } from "../../state/store";

/**
 * Playback cadence (UI §13): one step per beat, adjustable via `speed`
 * (0.5x–4x). Drives `advanceStep` on a `requestAnimationFrame` timer while
 * `playing`, and cancels the frame on pause/unmount (§B.6 — no timer leak).
 * Auto-pauses when the tab is hidden (§A.8).
 */
const FRAME_DURATION_MS = 600;

export function usePlayback(): void {
  const playing = useStore((s) => s.playing);
  const speed = useStore((s) => s.speed);
  const advanceStep = useStore((s) => s.advanceStep);
  const pause = useStore((s) => s.pause);

  useEffect(() => {
    if (!playing) return;
    let raf = 0;
    let last = 0;
    const duration = FRAME_DURATION_MS / speed;
    const tick = (now: number): void => {
      if (last === 0) last = now;
      if (now - last >= duration) {
        last = now;
        advanceStep();
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, speed, advanceStep]);

  useEffect(() => {
    const onVisibly = (): void => {
      if (document.hidden && useStore.getState().playing) {
        pause();
      }
    };
    document.addEventListener("visibilitychange", onVisibly);
    return () => document.removeEventListener("visibilitychange", onVisibly);
  }, [pause]);
}