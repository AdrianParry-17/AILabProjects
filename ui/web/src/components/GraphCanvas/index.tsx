import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { DeliveryEdge, DeliveryNode } from "../../api/types";
import {
  clientToView,
  composeTransform,
  createProjector,
  fitBounds,
  polylinePath,
  projectPolyline,
  toBounds,
  zoomAt,
  type InteractiveTransform,
  type Point,
} from "../../lib/coords";
import { kindLabel } from "../../lib/format";
import { frameAt } from "../../services/animation";
import { useStore } from "../../state/store";
import { EmptyState } from "../shared/EmptyState";
import { Spinner } from "../shared/Spinner";
import styles from "./index.module.css";
import { Legend } from "./Legend";
import { NodeListFallback } from "./NodeListFallback";
import { RouteOverlay } from "./RouteOverlay";

const FALLBACK_W = 1000;
const FALLBACK_H = 700;
const MIN_SCALE = 0.5;
const MAX_SCALE = 4;
const ZOOM_STEP = 1.15;
const IDLE_TRANSFORM: InteractiveTransform = { scale: 1, translateX: 0, translateY: 0 };

/** T08 fit-view transition: 220 ms, `--ease-panel` easing (MOTION §14). */
const FIT_DURATION_MS = 220;
const EASE_PANEL = cubicBezier(0.22, 1, 0.36, 1);

function cubicBezier(p1x: number, p1y: number, p2x: number, p2y: number): (t: number) => number {
  const sample = (t: number): [number, number] => {
    const u = 1 - t;
    return [
      3 * u * u * t * p1x + 3 * u * t * t * p2x + t * t * t,
      3 * u * u * t * p1y + 3 * u * t * t * p2y + t * t * t,
    ];
  };
  return (t: number): number => {
    let lo = 0;
    let hi = 1;
    for (let i = 0; i < 12; i += 1) {
      const mid = (lo + hi) / 2;
      const [x] = sample(mid);
      if (x < t) lo = mid;
      else hi = mid;
    }
    return sample((lo + hi) / 2)[1];
  };
}

/** Test-only render counters for the T09 memo acceptance: static-layer re-render
 *  counts must stay constant across playback steps (assert via `__staticRenderCounts`). */
export const __staticRenderCounts: { edges: number; nodes: number } = { edges: 0, nodes: 0 };

/** Static edge layer props — only the data the edge layer actually paints. */
interface EdgesLayerProps {
  nodes: readonly DeliveryNode[];
  edges: readonly DeliveryEdge[];
  transform: ReturnType<typeof fitBounds>;
}

/** Static node layer props. */
interface NodesLayerProps {
  nodes: readonly DeliveryNode[];
  transform: ReturnType<typeof fitBounds>;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
  path: readonly string[] | null;
}

/** Static edge layer — memoised, `pointer-events: none` (§C.2). */
export const EdgesLayer = memo(function EdgesLayer({
  nodes,
  edges,
  transform,
}: EdgesLayerProps): JSX.Element {
  __staticRenderCounts.edges += 1;
  const paths = useMemo(
    () =>
      edges.map((edge) => {
        const projector = createProjector(nodes, transform);
        const geometry = edge.attributes?.geometry;
        const points =
          Array.isArray(geometry) && geometry.length > 0
            ? projectPolyline(geometry, transform)
            : [projector.project(edge.start), projector.project(edge.end)];
        const valid = points.filter((p): p is Point => p !== undefined);
        return {
          key: edge.edge_id || `${edge.start}-${edge.end}`,
          d: polylinePath(valid),
        };
      }),
    [nodes, edges, transform],
  );

  return (
    <g className={styles.edgesLayer} aria-hidden="true">
      {paths.map((path) => (
        <path key={path.key} d={path.d} className={styles.edge} />
      ))}
    </g>
  );
});

/** Static node layer — memoised POI glyphs, click/hover/select (§C.2, §C.5, T09).
   Renders the *base* node style only; per-frame animation states (visited,
   current, frontier) are painted by `RouteOverlay` so this component never
   re-renders during playback. */
export const NodesLayer = memo(function NodesLayer({
  nodes,
  transform,
  selectedId,
  onSelect,
  onHover,
  path,
}: NodesLayerProps): JSX.Element {
  __staticRenderCounts.nodes += 1;
  const projector = useMemo(() => createProjector(nodes, transform), [nodes, transform]);
  const pathSet = useMemo(() => new Set(path ?? []), [path]);
  return (
    <g className={styles.nodesLayer}>
      {nodes.map((node) => {
        const pos = projector.project(node.id);
        if (!pos) return null;
        const selected = node.id === selectedId;
        const isStart = path != null && path.length > 0 && path[0] === node.id;
        const isGoal = path != null && path.length > 1 && path[path.length - 1] === node.id;
        const onPath = pathSet.has(node.id);
        const className = [
          styles.node,
          isStart ? styles.nodeStart : "",
          isGoal ? styles.nodeGoal : "",
          onPath ? styles.nodePath : "",
          selected ? styles.nodeSelected : "",
        ]
          .filter(Boolean)
          .join(" ");
        const dataState = selected
          ? "selected"
          : isStart
            ? "start"
            : isGoal
              ? "goal"
              : onPath
                ? "path"
                : "normal";
        return (
          <g
            key={node.id}
            className={styles.nodeGroup}
            transform={`translate(${pos.x} ${pos.y})`}
            onClick={() => onSelect(node.id)}
            onMouseEnter={() => onHover(node.id)}
            onMouseLeave={() => onHover(null)}
            role="button"
            tabIndex={0}
            aria-label={`${node.name} (${kindLabel(node.kind)})`}
            aria-selected={selected}
            data-node-id={node.id}
            data-state={dataState}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelect(node.id);
              }
            }}
          >
            <circle r={5} className={className} />
            <title>
              {node.name} ({kindLabel(node.kind)}) · {node.id}
            </title>
          </g>
        );
      })}
    </g>
  );
});

/**
 * GraphCanvas (§D.1). Store-driven: reads `graph`, `selectedNode`, `hoveredNode`,
 * and C1 animation state (`result` + `activeIndex` → `frameAt`). Paints memoised
 * Edges + Nodes layers, then the RouteOverlay, with pan (drag) and zoom (wheel)
 * manipulating view-space transforms; ResizeObserver keeps the viewBox in sync
 * with the container (Task-009 H1). Fallback viewBox used in jsdom / pre-mount.
 */
export function GraphCanvas(): JSX.Element {
  const graph = useStore((s) => s.graph);
  const status = useStore((s) => s.status);
  const selectedNode = useStore((s) => s.selectedNode);
  const selectNode = useStore((s) => s.selectNode);
  const setHoveredNode = useStore((s) => s.setHoveredNode);
  const result = useStore((s) => s.result);
  const activeIndex = useStore((s) => s.activeIndex);

  const wrapRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [interactive, setInteractive] = useState<InteractiveTransform>(IDLE_TRANSFORM);
  const interactiveRef = useRef(interactive);
  const fitAnimRef = useRef<number | null>(null);
  useEffect(() => {
    interactiveRef.current = interactive;
  }, [interactive]);
  const cancelFitAnim = useCallback(() => {
    if (fitAnimRef.current !== null) {
      cancelAnimationFrame(fitAnimRef.current);
      fitAnimRef.current = null;
    }
  }, []);
  useEffect(() => cancelFitAnim, [cancelFitAnim]);
  const dragRef = useRef<{ start: Point; tx: number; ty: number } | null>(null);

  const [viewBox, setViewBox] = useState({ w: FALLBACK_W, h: FALLBACK_H });
  useEffect(() => {
    const host = wrapRef.current;
    if (!host || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver((entries) => {
      const rect = entries[0]?.contentRect;
      if (rect && rect.width > 0 && rect.height > 0) {
        setViewBox({ w: rect.width, h: rect.height });
      }
    });
    observer.observe(host);
    return () => observer.disconnect();
  }, []);

  const fit = useMemo(() => {
    if (!graph) return null;
    return fitBounds(toBounds(graph.bbox), viewBox.w, viewBox.h);
  }, [graph, viewBox]);

  const viewTransform = useMemo(
    () => (fit ? composeTransform(fit, interactive) : null),
    [fit, interactive],
  );

  const frame = useMemo(() => {
    if (!result) return null;
    return frameAt(result.steps, activeIndex);
  }, [result, activeIndex]);

  const onWheel = useCallback(
    (e: WheelEvent) => {
      e.preventDefault();
      cancelFitAnim();
      const svg = svgRef.current;
      if (!svg) return;
      const factor = e.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP;
      const anchor = clientToView(svg, e.clientX, e.clientY);
      setInteractive((prev) => zoomAt(prev, factor, anchor, MIN_SCALE, MAX_SCALE));
    },
    [cancelFitAnim],
  );

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    svg.addEventListener("wheel", onWheel, { passive: false });
    return () => svg.removeEventListener("wheel", onWheel);
  }, [onWheel]);

  const onPointerDown = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (e.button !== 0) return;
      cancelFitAnim();
      const target = e.target as Element;
      if (target.closest(`.${styles.nodeGroup}`)) return;
      dragRef.current = {
        start: clientToView(svgRef.current as SVGSVGElement, e.clientX, e.clientY),
        tx: interactive.translateX,
        ty: interactive.translateY,
      };
      (e.currentTarget as SVGSVGElement).setPointerCapture(e.pointerId);
    },
    [interactive.translateX, interactive.translateY],
  );

  const onPointerMove = useCallback((e: React.PointerEvent<SVGSVGElement>) => {
    const drag = dragRef.current;
    if (!drag) return;
    const view = clientToView(svgRef.current as SVGSVGElement, e.clientX, e.clientY);
    setInteractive((prev) => ({
      ...prev,
      translateX: drag.tx + view.x - drag.start.x,
      translateY: drag.ty + view.y - drag.start.y,
    }));
  }, []);

  const onPointerUp = useCallback(() => {
    dragRef.current = null;
  }, []);

  const fitView = useCallback(() => {
    cancelFitAnim();
    const reduced =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const from = interactiveRef.current;
    if (reduced || from === IDLE_TRANSFORM || (from.scale === 1 && from.translateX === 0 && from.translateY === 0)) {
      setInteractive(IDLE_TRANSFORM);
      return;
    }
    const start = performance.now();
    const tick = (now: number): void => {
      const t = Math.min((now - start) / FIT_DURATION_MS, 1);
      const eased = EASE_PANEL(t);
      setInteractive({
        scale: from.scale + (1 - from.scale) * eased,
        translateX: from.translateX * (1 - eased),
        translateY: from.translateY * (1 - eased),
      });
      fitAnimRef.current = t < 1 ? requestAnimationFrame(tick) : null;
    };
    fitAnimRef.current = requestAnimationFrame(tick);
  }, [cancelFitAnim]);
  const zoomIn = useCallback(
    () => setInteractive((p) => zoomAt(p, ZOOM_STEP, { x: viewBox.w / 2, y: viewBox.h / 2 }, MIN_SCALE, MAX_SCALE)),
    [viewBox],
  );
  const zoomOut = useCallback(
    () => setInteractive((p) => zoomAt(p, 1 / ZOOM_STEP, { x: viewBox.w / 2, y: viewBox.h / 2 }, MIN_SCALE, MAX_SCALE)),
    [viewBox],
  );

  if (status === "Loading") {
    return <Spinner />;
  }
  if (!graph || !viewTransform) {
    return <EmptyState title="No graph data" subtitle="Could not load graph data." />;
  }

  return (
    <div ref={wrapRef} className={styles.wrap}>
      <svg
        ref={svgRef}
        className={styles.canvas}
        viewBox={`0 0 ${viewBox.w} ${viewBox.h}`}
        role="img"
        aria-label="Map of delivery points"
        data-testid="graph-canvas"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onDoubleClick={fitView}
        tabIndex={-1}
      >
        <rect x={0} y={0} width={viewBox.w} height={viewBox.h} className={styles.basePlate} />
        <EdgesLayer
          nodes={graph.nodes}
          edges={graph.edges}
          transform={viewTransform}
        />
        {result && frame && (
          <RouteOverlay
            nodes={graph.nodes}
            edges={graph.edges}
            transform={viewTransform}
            path={result.path}
            frame={frame}
          />
        )}
        <NodesLayer
          nodes={graph.nodes}
          transform={viewTransform}
          selectedId={selectedNode}
          onSelect={selectNode}
          onHover={setHoveredNode}
          path={result?.path ?? null}
        />
      </svg>
      <div className={styles.controls}>
        <button type="button" className={styles.control} onClick={zoomIn} aria-label="Zoom In">
          +
        </button>
        <button type="button" className={styles.control} onClick={zoomOut} aria-label="Zoom Out">
          −
        </button>
        <button type="button" className={styles.control} onClick={fitView} aria-label="Fit Graph">
          fit
        </button>
      </div>
      {result && frame && <Legend />}
      <NodeListFallback nodes={graph.nodes} selectedId={selectedNode} onSelect={selectNode} />
    </div>
  );
}