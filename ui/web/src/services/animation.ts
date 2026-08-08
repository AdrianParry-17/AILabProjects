/**
 * Animation reducer (COMPONENT_SPEC.md §2.9 AnimationEngine, GUI_ROADMAP §9).
 *
 * Pure, algorithm-agnostic: it never inspects the algorithm name — a `Step`
 * only carries `current_node`, `frontier` and `reason` (MAP_CONTRACT §3.2).
 * A `Frame` is one rendered instant: the current node, the live frontier, the
 * running set of visited ids, and the caption. `applyFrame` folds one `Step`
 * into a `Frame`; callers drive the animation by feeding steps in order.
 */

export interface Frame {
  /** Index of the last applied step (monotonic, -1 before any step). */
  index: number;
  /** Node currently expanded (or null before the first step). */
  current: string | null;
  /** Frontier node ids at this instant. */
  frontierIds: string[];
  /** All nodes visited so far, in expansion order, without duplicates. */
  visitedIds: string[];
  /** Reason caption of the last applied step. */
  reason: string;
  /** True once every step has been consumed. */
  isDone: boolean;
}

/** The wire shape of one `SearchStep` (MAP_CONTRACT §3.1/§3.2). */
export interface Step {
  current_node: string;
  frontier: string[];
  reason: string;
}

/** The frame before any step has been applied. */
export function initialFrame(): Frame {
  return {
    index: -1,
    current: null,
    frontierIds: [],
    visitedIds: [],
    reason: "",
    isDone: false,
  };
}

/** True when `steps` is empty (trivial search; no animation, §3.2). */
export function isEmpty(steps: Step[]): boolean {
  return steps.length === 0;
}

/** Whether `prev` has consumed all `steps`. */
export function isDone(frame: Frame, steps: Step[]): boolean {
  return frame.isDone || frame.index >= steps.length - 1;
}

/**
 * Fold `step` into `prev`, appending the current node to the visited set (no
 * duplicates) and exposing the live frontier + reason caption.
 */
export function applyFrame(prev: Frame, step: Step): Frame {
  const visitedIds = prev.visitedIds.includes(step.current_node)
    ? prev.visitedIds
    : [...prev.visitedIds, step.current_node];
  return {
    index: prev.index + 1,
    current: step.current_node,
    frontierIds: [...step.frontier],
    visitedIds,
    reason: step.reason,
    isDone: false,
  };
}

/**
 * Reduce `steps` onto a fresh initial frame, one `applyFrame` at a time. The
 * returned frame's `index` equals `steps.length - 1` (or -1 for empty input).
 */
export function reduceSteps(steps: Step[]): Frame {
  return steps.reduce(applyFrame, initialFrame());
}

/**
 * Return the frame to show when the animation has advanced to step `at`
 * (0 <= at < steps.length), or the initial frame when `steps` is empty.
 * Replaying the same steps always yields the same result (algorithm-agnostic).
 */
export function frameAt(steps: Step[], at: number): Frame {
  if (isEmpty(steps)) {
    return initialFrame();
  }
  const clamped = Math.max(0, Math.min(at, steps.length - 1));
  return reduceSteps(steps.slice(0, clamped + 1));
}