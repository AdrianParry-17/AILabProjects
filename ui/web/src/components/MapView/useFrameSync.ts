import { useMemo } from "react";

import type { SearchResult } from "../../api/types";
import { frameAt } from "../../services/animation";

/**
 * useFrameSync (UI_IMPLEMENTATION_PLAN §7 T12): the ONLY Frame derivation in
 * the map renderer. It calls the existing `frameAt(steps, activeIndex)` from
 * `ui/web/src/services/animation.ts` — the exact reducer the Graph renderer
 * consumes — so both renderers always represent the same SearchStep state.
 * No duplicated animation state lives in MapView.
 */
export function useFrameSync(
  result: SearchResult | null,
  activeIndex: number,
): ReturnType<typeof frameAt> {
  return useMemo(() => {
    if (!result) return frameAt([], -1);
    return frameAt(result.steps, activeIndex);
  }, [result, activeIndex]);
}