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
import { MapOverlays } from "./Overlays";
import { useFrameSync } from "./useFrameSync";
import { useLeaflet } from "./useLeaflet";
import styles from "./index.module.css";

/**
 * MapView (UI_IMPLEMENTATION_PLAN §7 T11–T13). The street-map renderer:
 * pure presentational shell — no graph/search logic, no API calls. All state
 * comes from the store (`graph`, `result` + `activeIndex` via the shared
 * `useFrameSync`, `selectedNode`, `start`/`goal`, `setStart`/`setGoal`).
 * Switching renderers is a store change; mounting/unmounting never reruns
 * search nor resets playback.
 *
 * Interactions: leaflet-native wheel zoom, drag, double-click zoom, touch
 * pinch, keyboard; floating controls: +, −, Fit, Locate Graph.
 * Camera: initial fit of the graph bounds (40 px padding), clamped to
 * [10, 18]; the camera survives renderer switches via `useLeaflet`'s cache.
 */
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
        setHoverNode(nodesById.get(id) ?? null);
        setHoverPoint(point);
      } else {
        setHoverNode(null);
        setHoverPoint(null);
      }
    },
    [nodesById, setHoveredNode],
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

  if (status === "Loading") {
    return (
      <div className={styles.overlayWrap} data-testid="map-view">
        <div className={styles.skeletonMap} data-testid="map-skeleton" aria-busy="true" />
      </div>
    );
  }
  if (!graph || status === "Error") {
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

  return (
    <div className={styles.overlayWrap} data-testid="map-view">
      {!tilesLoaded ? (
        <div className={styles.skeletonMap} data-testid="map-skeleton" aria-busy="true" />
      ) : null}
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
    </div>
  );
}

/** Clamp to the shared camera limits (MAP_RENDERING_SPEC §4). */
function clampZoom(zoom: number): number {
  return Math.max(10, Math.min(18, zoom));
}