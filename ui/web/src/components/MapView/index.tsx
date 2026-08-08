import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import L from "leaflet";

import type { DeliveryNode } from "../../api/types";
import { toBounds } from "../../lib/coords";
import { kindLabel } from "../../lib/format";
import { useStore } from "../../state/store";
import { Button } from "../shared/Button";
import { EmptyState } from "../shared/EmptyState";
import { Popup, type PopupNode } from "../shared/Popup";
import { Tooltip } from "../shared/Tooltip";
import { NodeListFallback } from "../GraphCanvas/NodeListFallback";
import { MapOverlays } from "./Overlays";
import { useFrameSync } from "./useFrameSync";
import { useLeaflet, type MapInstance } from "./useLeaflet";
import styles from "./index.module.css";

/**
 * MapView (UI_IMPLEMENTATION_PLAN §7 T11–T13). The street-map renderer:
 * pure presentational shell — no graph/search logic, no API calls. All state
 * comes from the store (`graph`, `result` + `activeIndex` via the shared
 * `useFrameSync`, `selectedNode`, `start`/`goal`, `setStart`/`setGoal`).
 * Switching renderers is a store change; mounting/unmounting never reruns
 * search nor resets playback.
 *
 * Lifecycle (T11): once a graph exists the Leaflet container stays mounted
 * across Loading/Ready/Error — search, retry and error recovery overlay the
 * map instead of destroying it, so the `useLeaflet` instance never orphanes
 * on a detached DOM node.
 *
 * Interactions: leaflet-native wheel zoom, drag, double-click zoom, touch
 * pinch, keyboard; floating controls: +, −, Fit, Locate Graph; keyboard
 * accessible node list (shared NodeListFallback).
 * Camera: initial fit of the graph bounds (40 px padding), clamped to
 * [10, 18]; the camera survives renderer switches via `useLeaflet`'s cache.
 */

/**
 * Tooltip anchor resolution (T13/F8): markers report the hover point when
 * Leaflet provides one; pins and the current node call back with `null`, so
 * the anchor is derived from the node's container position. Pure — no Leaflet
 * instance is required until the call.
 */
export function resolveHoverPoint(
  view: MapInstance | null,
  node: DeliveryNode | null,
  point: { x: number; y: number } | null,
): { x: number; y: number } | null {
  if (point) return point;
  if (!view || !node) return null;
  const p = view.map.latLngToContainerPoint([node.latitude, node.longitude]);
  return { x: p.x, y: p.y };
}

export function MapView(): JSX.Element {
  const status = useStore((s) => s.status);
  const error = useStore((s) => s.error);
  const graph = useStore((s) => s.graph);
  const result = useStore((s) => s.result);
  const activeIndex = useStore((s) => s.activeIndex);
  const start = useStore((s) => s.start);
  const goal = useStore((s) => s.goal);
  const setStart = useStore((s) => s.setStart);
  const setGoal = useStore((s) => s.setGoal);
  const selectNode = useStore((s) => s.selectNode);
  const setHoveredNode = useStore((s) => s.setHoveredNode);
  const selectedNode = useStore((s) => s.selectedNode);
  const loadGraph = useStore((s) => s.loadGraph);

  const frame = useFrameSync(result, activeIndex);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const bounds = useMemo(() => (graph ? toBounds(graph.bbox) : null), [graph]);
  const { view } = useLeaflet(containerRef, bounds);

  const [tilesLoaded, setTilesLoaded] = useState(false);
  const [popupNode, setPopupNode] = useState<PopupNode | null>(null);
  const [hoverNode, setHoverNode] = useState<DeliveryNode | null>(null);
  const [hoverPoint, setHoverPoint] = useState<{ x: number; y: number } | null>(null);

  const nodesById = useMemo(
    () => new Map((graph?.nodes ?? []).map((n) => [n.id, n] as const)),
    [graph],
  );

  /** First-tile load fades the skeleton out (spec §22 loading state). */
  useEffect(() => {
    if (!view || tilesLoaded) return;
    const handle = (): void => setTilesLoaded(true);
    view.tileLayer.once("load", handle);
    return () => {
      view.tileLayer.off("load", handle);
    };
  }, [view, tilesLoaded]);

  const fitMap = useCallback(() => {
    if (!view || !bounds) return;
    view.map.fitBounds(
      L.latLngBounds([bounds.minLat, bounds.minLon], [bounds.maxLat, bounds.maxLon]),
      { padding: [40, 40], maxZoom: 18 },
    );
  }, [view, bounds]);

  const locateGraph = useCallback(() => {
    if (!view || !bounds) return;
    view.map.panTo([(bounds.minLat + bounds.maxLat) / 2, (bounds.minLon + bounds.maxLon) / 2]);
  }, [view, bounds]);

  const zoomStep = useCallback(
    (delta: number) => {
      if (!view) return;
      view.map.setZoom(clampZoom(view.map.getZoom() + delta));
    },
    [view],
  );

  const onMarkerClick = useCallback(
    (id: string) => {
      const node = nodesById.get(id);
      selectNode(id);
      if (node) {
        setPopupNode({
          id: node.id,
          name: node.name,
          kind: node.kind,
          latitude: node.latitude,
          longitude: node.longitude,
        });
      }
    },
    [nodesById, selectNode],
  );

  const onMarkerHover = useCallback(
    (id: string | null, point: { x: number; y: number } | null) => {
      setHoveredNode(id);
      if (id) {
        const node = nodesById.get(id) ?? null;
        setHoverNode(node);
        setHoverPoint(resolveHoverPoint(view, node, point));
      } else {
        setHoverNode(null);
        setHoverPoint(null);
      }
    },
    [nodesById, setHoveredNode, view],
  );

  const centerHere = useCallback(() => {
    if (!view || !popupNode) return;
    view.map.panTo([popupNode.latitude, popupNode.longitude]);
  }, [view, popupNode]);

  /** Popup anchored over its node, re-measured after each pan/zoom commit. */
  const [, setMapTick] = useState(0);
  useEffect(() => {
    if (!view) return;
    const bump = (): void => setMapTick((t) => t + 1);
    view.map.on("moveend zoomend", bump);
    return () => {
      view.map.off("moveend zoomend", bump);
    };
  }, [view]);
  const popupStyle = useMemo(() => {
    if (!view || !popupNode) return undefined;
    const point = view.map.latLngToContainerPoint([
      popupNode.latitude,
      popupNode.longitude,
    ]);
    return { left: point.x, top: point.y, transform: "translate(-50%, -115%)" };
  }, [view, popupNode]);

  // Before any graph exists the map host cannot be created (no bounds):
  // Loading shows a skeleton, everything else shows the shared EmptyState.
  if (status === "Loading" && !graph) {
    return (
      <div className={styles.overlayWrap} data-testid="map-view">
        <div className={styles.skeletonMap} data-testid="map-skeleton" aria-busy="true" />
      </div>
    );
  }
  if (!graph) {
    return (
      <div className={styles.overlayWrap} data-testid="map-view">
        <EmptyState
          title={status === "Error" ? "Graph load failed" : "No graph loaded"}
          subtitle={status === "Error" ? (error ?? "Could not load graph data.") : "Load graph to begin."}
          action={status === "Error" ? <Button onClick={() => void loadGraph()}>Retry</Button> : undefined}
        />
      </div>
    );
  }

  const startId = result && result.path.length > 0 ? result.path[0] : start;
  const goalId = result && result.path.length > 1 ? result.path[result.path.length - 1] : goal;

  // Loading (search/retry) and pre-tile states overlay the map instead of
  // unmounting the Leaflet host — the container must stay mounted so the
  // useLeaflet instance is never orphaned on a detached node (T11 lifecycle).
  const showSkeleton = !tilesLoaded || status === "Loading";

  return (
    <div className={styles.overlayWrap} data-testid="map-view">
      <div
        ref={containerRef}
        className={styles.map}
        role="application"
        aria-label="Street map of delivery points"
        data-testid="map-canvas"
      />
      <MapOverlays
        map={view}
        nodes={nodesById}
        edges={graph.edges}
        frame={frame}
        path={result?.path ?? null}
        startId={startId}
        goalId={goalId}
        onMarkerClick={onMarkerClick}
        onMarkerHover={onMarkerHover}
      />
      {view ? (
        <div className={styles.controls}>
          <button type="button" className={styles.control} aria-label="Zoom In" onClick={() => zoomStep(1)}>
            +
          </button>
          <button type="button" className={styles.control} aria-label="Zoom Out" onClick={() => zoomStep(-1)}>
            −
          </button>
          <button type="button" className={styles.control} aria-label="Fit Graph" onClick={fitMap}>
            fit
          </button>
          <button type="button" className={styles.control} aria-label="Locate Graph" onClick={locateGraph}>
            locate
          </button>
        </div>
      ) : null}
      {/* Keyboard-reachable node proxy (T13/F5): same rows/actions as the
          Graph renderer's fallback list; clicking a row selects + opens the
          same Popup as a marker click. */}
      <NodeListFallback nodes={graph.nodes} selectedId={selectedNode} onSelect={onMarkerClick} />
      {hoverNode && hoverPoint && view ? (
        <div className={styles.hoverAnchor} style={{ left: hoverPoint.x, top: hoverPoint.y }}>
          <Tooltip
            open
            title={hoverNode.name}
            lines={[
              { label: "ID", value: hoverNode.id },
              { label: "Type", value: kindLabel(hoverNode.kind) },
              {
                label: "Coords",
                value: `${hoverNode.latitude.toFixed(4)}, ${hoverNode.longitude.toFixed(4)}`,
              },
            ]}
          />
        </div>
      ) : null}
      {popupNode && popupStyle ? (
        <Popup
          node={popupNode}
          style={popupStyle}
          onSetStart={(id) => {
            setStart(id);
            setPopupNode(null);
          }}
          onSetGoal={(id) => {
            setGoal(id);
            setPopupNode(null);
          }}
          onCenter={centerHere}
          onClose={() => setPopupNode(null)}
        />
      ) : null}
      {showSkeleton ? (
        <div className={styles.skeletonMap} data-testid="map-skeleton" aria-busy="true" />
      ) : null}
      {status === "Error" ? (
        <div className={styles.errorDim} data-testid="map-error" role="status">
          <EmptyState
            title="Graph load failed"
            subtitle={error ?? "Could not load graph data."}
            action={<Button onClick={() => void loadGraph()}>Retry</Button>}
          />
        </div>
      ) : null}
    </div>
  );
}

/** Clamp to the shared camera limits (MAP_RENDERING_SPEC §4). */
function clampZoom(zoom: number): number {
  return Math.max(10, Math.min(18, zoom));
}