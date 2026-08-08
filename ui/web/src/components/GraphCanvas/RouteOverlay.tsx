import { useMemo } from "react";

import type { DeliveryEdge, DeliveryNode } from "../../api/types";
import {
  createProjector,
  polylinePath,
  type Point,
  type Projector,
  type ViewTransform,
} from "../../lib/coords";
import type { Frame } from "../../services/animation";
import styles from "./index.module.css";

/**
 * RouteOverlay (UI_IMPLEMENTATION_PLAN §7 T09, MAP_RENDERING §8–15): the only
 * consumer of animation state on the canvas. Paints visited edges, the current
 * traversal edge, the resolved route (final path), persistent start/goal
 * gateway rings, and per-frame markers (visited → frontier → current), all in
 * view-space units via a projector.
 *
 * Layer order (LAYOUT_SPEC §23): visited-edge → current-edge → route halo →
 * route → visited nodes → frontier → current → start/goal rings.
 * The overlay is rendered between `EdgesLayer` and `NodesLayer` so the base
 * nodes paint over visited/path markers (per spec: visited → path below nodes).
 *
 * Edge authenticity (review M1): only consecutive visited ids connected by a
 * real graph edge are drawn as visited polyline segments; same for current →
 * frontier[0]. Prevents drawing chords between nodes that the graph never
 * connected (e.g. BFS queue order ≠ graph adjacency).
 */
export function RouteOverlay({
  nodes,
  edges,
  transform,
  path,
  frame,
}: {
  nodes: readonly DeliveryNode[];
  edges: readonly DeliveryEdge[];
  transform: ViewTransform;
  path: readonly string[] | null;
  frame: Frame;
}): JSX.Element {
  const projector = useMemo(() => createProjector(nodes, transform), [nodes, transform]);

  /** O(1) adjacency lookup so the visited/current edges filter by real edges.
   *  Stored unordered (`min|max`) so traversal direction is irrelevant. */
  const adjacency = useMemo(() => {
    const set = new Set<string>();
    for (const e of edges) {
      const [lo, hi] = e.start < e.end ? [e.start, e.end] : [e.end, e.start];
      set.add(`${lo}|${hi}`);
    }
    return set;
  }, [edges]);

  /** True iff the graph has an edge between `a` and `b`. */
  const isAdjacent = (a: string, b: string): boolean => {
    const [lo, hi] = a < b ? [a, b] : [b, a];
    return adjacency.has(`${lo}|${hi}`);
  };

  /** Project every pair of consecutive visited ids into a polyline, but only
   *  when the pair is actually connected by an edge. */
  const visitedEdges = useMemo(() => {
    if (frame.visitedIds.length < 2) return [];
    const points: Point[] = [];
    for (let i = 0; i < frame.visitedIds.length - 1; i += 1) {
      const aId = frame.visitedIds[i];
      const bId = frame.visitedIds[i + 1];
      if (!isAdjacent(aId, bId)) continue;
      const a = projector.project(aId);
      const b = projector.project(bId);
      if (a && b) points.push(a, b);
    }
    return points;
  }, [frame.visitedIds, projector, adjacency]);

  /** Edge from the current node to the next frontier node — only when it is
   *  actually a graph edge (otherwise the polyline would invent a link). */
  const currentEdge = useMemo(() => {
    if (!frame.current || frame.frontierIds.length === 0) return null;
    const next = frame.frontierIds[0];
    if (!isAdjacent(frame.current, next)) return null;
    const a = projector.project(frame.current);
    const b = projector.project(next);
    return a && b ? { a, b } : null;
  }, [frame.current, frame.frontierIds, projector, adjacency]);

  const routePoints = useMemo(() => {
    if (!path || path.length < 2) return null;
    return path
      .map((id) => projector.project(id))
      .filter((p): p is NonNullable<ReturnType<Projector["project"]>> => p !== undefined);
  }, [path, projector]);

  const frontier = useMemo(
    () =>
      frame.frontierIds
        .map((id) => projector.project(id))
        .filter((p): p is NonNullable<ReturnType<Projector["project"]>> => p !== undefined),
    [frame.frontierIds, projector],
  );

  const visited = useMemo(
    () =>
      frame.visitedIds
        .map((id) => projector.project(id))
        .filter((p): p is NonNullable<ReturnType<Projector["project"]>> => p !== undefined),
    [frame.visitedIds, projector],
  );

  /** Path-member nodes (final path) — distinct from visited-only nodes. */
  const pathNodes = useMemo(() => {
    if (!path || path.length === 0) return [];
    return path
      .map((id) => projector.project(id))
      .filter((p): p is NonNullable<ReturnType<Projector["project"]>> => p !== undefined);
  }, [path, projector]);

  const current = useMemo(
    () => (frame.current ? projector.project(frame.current) ?? null : null),
    [frame.current, projector],
  );

  const start = useMemo(() => {
    const first = path && path.length > 0 ? projector.project(path[0]) : undefined;
    return first ?? null;
  }, [path, projector]);

  const goal =
    path && path.length > 1 ? projector.project(path[path.length - 1]) ?? null : null;

  return (
    <g className={styles.overlayLayer} aria-hidden={!routePoints}>
      {visitedEdges.length > 1 && (
        <polyline
          points={polylinePath(visitedEdges)}
          className={styles.visitedEdge}
          fill="none"
        />
      )}

      {currentEdge && (
        <line
          x1={currentEdge.a.x}
          y1={currentEdge.a.y}
          x2={currentEdge.b.x}
          y2={currentEdge.b.y}
          className={styles.currentEdge}
        />
      )}

      {routePoints && (
        <>
          <polyline
            points={polylinePath(routePoints)}
            className={styles.routeHalo}
            fill="none"
          />
          <polyline
            points={polylinePath(routePoints)}
            className={styles.route}
            fill="none"
          />
        </>
      )}

      {visited.map((p, i) => (
        <circle key={`v-${i}`} cx={p.x} cy={p.y} r={6} className={styles.visitedMark} />
      ))}

      {frontier.map((p, i) => (
        <circle key={`f-${i}`} cx={p.x} cy={p.y} r={8} className={styles.frontierMark} />
      ))}

      {pathNodes.map((p, i) => (
        <circle key={`p-${i}`} cx={p.x} cy={p.y} r={6} className={styles.pathMark} />
      ))}

      {current && (
        <circle cx={current.x} cy={current.y} r={9} className={styles.currentMark} />
      )}

      {start && (
        <g className={styles.gatewayMark}>
          <circle cx={start.x} cy={start.y} r={11} className={styles.gatewayRing} />
          <circle cx={start.x} cy={start.y} r={2.5} className={styles.gatewayCore} />
        </g>
      )}
      {goal && (
        <g className={styles.gatewayMark}>
          <circle cx={goal.x} cy={goal.y} r={11} className={styles.gatewayRingGoal} />
          <circle cx={goal.x} cy={goal.y} r={2.5} className={styles.gatewayCoreGoal} />
        </g>
      )}
    </g>
  );
}
