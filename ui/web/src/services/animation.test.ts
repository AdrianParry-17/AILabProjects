import { describe, expect, it } from "vitest";

import {
  applyFrame,
  frameAt,
  initialFrame,
  isDone,
  reduceSteps,
  type Step,
} from "./animation";

function step(currentNode: string, frontier: string[], reason = "expand"): Step {
  return { current_node: currentNode, frontier, reason };
}

describe("initialFrame", () => {
  it("starts empty and not done", () => {
    const frame = initialFrame();
    expect(frame.index).toBe(-1);
    expect(frame.current).toBeNull();
    expect(frame.frontierIds).toEqual([]);
    expect(frame.visitedIds).toEqual([]);
    expect(frame.reason).toBe("");
    expect(frame.isDone).toBe(false);
  });
});

describe("applyFrame", () => {
  it("advances the index and marks the current node visited", () => {
    const prev = initialFrame();
    const next = applyFrame(prev, step("n2", ["n3", "n4"], "found next"));
    expect(next.index).toBe(0);
    expect(next.current).toBe("n2");
    expect(next.frontierIds).toEqual(["n3", "n4"]);
    expect(next.visitedIds).toEqual(["n2"]);
    expect(next.reason).toBe("found next");
  });

  it("accumulates visited ids without duplicates", () => {
    const a = applyFrame(initialFrame(), step("n1", ["n2"], "x"));
    const b = applyFrame(a, step("n2", ["n3"], "y"));
    expect(b.visitedIds).toEqual(["n1", "n2"]);
    const c = applyFrame(b, step("n2", ["n3"], "y"));
    expect(c.visitedIds).toEqual(["n1", "n2"]);
  });

  it("monotonic index across consecutive frames", () => {
    const steps = [step("n1", ["n2"]), step("n2", ["n3"]), step("n3", [])];
    const last = reduceSteps(steps);
    expect(last.index).toBe(2);
  });
});

describe("isDone", () => {
  it("is false before the last step and true at it", () => {
    const steps = [step("n1", ["n2"]), step("n2", [])];
    const one = applyFrame(initialFrame(), steps[0]);
    expect(isDone(one, steps)).toBe(false);
    const two = applyFrame(one, steps[1]);
    expect(isDone(two, steps)).toBe(true);
  });

  it("is true when a frame is already flagged done", () => {
    const frame = { ...reduceSteps([]), isDone: true };
    expect(isDone(frame, [step("n1", [])])).toBe(true);
  });

  it("empty steps: initial frame is done", () => {
    expect(isDone(initialFrame(), [])).toBe(true);
  });
});

describe("reduceSteps + frameAt", () => {
  it("reduceSteps folds all steps in order", () => {
    const steps = [step("n1", ["n2"]), step("n2", ["n3"]), step("n3", [])];
    const frame = reduceSteps(steps);
    expect(frame.index).toBe(2);
    expect(frame.current).toBe("n3");
    expect(frame.visitedIds).toEqual(["n1", "n2", "n3"]);
  });

  it("frameAt clamps out-of-range indices", () => {
    const steps = [step("n1", ["n2"]), step("n2", [])];
    expect(frameAt(steps, -5).index).toBe(0);
    expect(frameAt(steps, 99).index).toBe(1);
  });

  it("replays the same steps to the same frame (algorithm-independent)", () => {
    const steps = [step("a", ["b"]), step("b", ["c"])];
    const first = frameAt(steps, 1);
    const second = frameAt(steps, 1);
    expect(first).toEqual(second);
  });
});
