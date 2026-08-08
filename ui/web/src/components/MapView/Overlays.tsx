import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";

import type { DeliveryEdge, DeliveryNode } from "../../api/types";
import type { Frame } from "../../services/animation";
import type { MapInstance } from "./useLeaflet";
import styles from "./index.module.css";

/**
 * Map overlays (UI_IMPLEMENTATION_PLAN §7 T12, MAP_RENDERING_SPEC §7–§15).
 * Builds Leaflet vector layers on top of the tiles:
 *
 *   tiles → road graph → animated route → visited → current → start/goal
 *
 * Rendering is driven exclusively by the shared `Frame` + `result.path`
 * (store + `frameAt`); this module never derives animation state and contains
 * no search/algorithm logic.
 *
 * jsdom safety: without a map instance every layer is skipped and the element
 * exposes a data summary (`data-visited`, `data-current`, `data-route`) that
 * tests assert against — the Leaflet path stays inert in the test env.
 */

/** Read a --c-* design token as a usable color string for Leaflet options. */
function tokenColor(name: string, fallback: string): string {
  if (typeof document === "undefined" || typeof getComputedStyle !== "function") {
    return fallback;
  }
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

/** Progressive route (MAP_RENDERING_SPEC §9): the number of path vertices
 *  already visited by the Frame — the route "draws" as playback advances.
 *  Pure and unit-testable. */
export function progressiveRoute(
  path: readonly string[] | null,
  visitedIds: readonly string[],
): number {
  if (!path || path.length === 0) return 0;
  const visited = new Set(visitedIds);
  let count = 0;
  for (const id of path) {
    if (visited.has(id)) count += 1;
    else break;
  }
  return count;
}

/** Convert a delivery edge into a `[lat, lng][]` polyline for Leaflet. */
export function edgeLatLngs(
  edge: DeliveryEdge,
  nodes: ReadonlyMap<string, DeliveryNode>,
): [number, number][] | null {
  const geometry = edge.attributes?.geometry;
  if (Array.isArray(geometry) && geometry.length > 0) {
    return geometry.map(
      ([lon, lat]) => [lat, lon] as [number, number],
    );
  }
  const start = nodes.get(edge.start);
  const end = nodes.get(edge.end);
  if (!start || !end) return null;
  return [
    [start.latitude, start.longitude],
    [end.latitude, end.longitude],
  ];
}

interface MapOverlaysProps {
  map: MapInstance | null;
  nodes: ReadonlyMap<string, DeliveryNode>;
  edges: readonly DeliveryEdge[];
  frame: Frame;
  path: readonly string[] | null;
  startId: string | null;
  goalId: string | null;
  onMarkerClick: (id: string) => void;
  onMarkerHover: (id: string | null, point: { x: number; y: number } | null) => void;
}

/**
 * Renders the graph over the map. Each effect guards on `map`; the returned
 * element is an (invisible) data summary used by tests — the visible work is
 * performed imperatively on Leaflet layers.
 */
export function MapOverlays({
  map,
  nodes,
  edges,
  frame,
  path,
  startId,
  goalId,
  onMarkerClick,
  onMarkerHover,
}: MapOverlaysProps): JSX.Element {
  const visitedIds = frame.visitedIds;
  const currentId = frame.current;
  const routeLen = useMemo(() => progressiveRoute(path, visitedIds), [path, visitedIds]);

  /** Road graph (static): rebuilt only when the graph data changes. */
  useEffect(() => {
    if (!map) return;
    const layer = L.layerGroup().addTo(map.map);
    const svg = L.svg();
    for (const edge of edges) {
      const points = edgeLatLngs(edge, nodes);
      if (!points || points.length < 2) continue;
      L.polyline(points, {
        color: tokenColor("--color-gray-400", "#a8b4be"),
        opacity: 0.55,
        weight: 2,
        interactive: false,
        renderer: svg,
      }).addTo(layer);
    }
    return () => {
      layer.removeFrom(map.map);
    };
  }, [map, edges, nodes]);

  /** Current node id of the previous frame — a change means the current node
   *  was just entered and its entry pulse may fire once (MOTION_SPEC §18:
   *  pulse fires once on entry, never infinite). */
  const prevCurrentIdRef = useRef<string | null>(null);

  /** Per-frame animated layers: progressive route, visited, current. */
  useEffect(() => {
    if (!map) return;
    const layer = L.layerGroup().addTo(map.map);

    const justEntered = prevCurrentIdRef.current !== currentId;
    prevCurrentIdRef.current = currentId;

    const routeIds = routeLen > 0 ? path!.slice(0, routeLen) : [];
    if (routeIds.length > 1) {
      const lats = routeIds
        .map((id) => nodes.get(id))
        .filter((n): n is DeliveryNode => n !== undefined)
        .map((n) => [n.latitude, n.longitude] as [number, number]);
      if (lats.length > 0) {
        L.polyline(lats, {
          color: tokenColor("--color-info-300", "#6bb3da"),
          weight: 10,
          opacity: 0.25,
          lineCap: "round",
          className: styles.routeGlow,
          interactive: false,
          renderer: L.svg(),
        }).addTo(layer);
        L.polyline(lats, {
          color: tokenColor("--color-info-500", "#2b86b7"),
          weight: 5,
          opacity: 0.95,
          lineCap: "round",
          lineJoin: "round",
          className: styles.route,
          interactive: false,
          renderer: L.svg(),
        }).addTo(layer);
      }
    }

    const sharedSvg = L.svg();
    for (const id of visitedIds) {
      const node = nodes.get(id);
      if (!node) continue;
      L.circleMarker([node.latitude, node.longitude], {
        radius: 5,
        color: tokenColor("--color-info-500", "#2b86b7"),
        fillColor: tokenColor("--color-info-500", "#2b86b7"),
        fillOpacity: 0.35,
        weight: 1,
        interactive: true,
        renderer: sharedSvg,
      })
        .on("click", () => onMarkerClick(id))
        .on("mouseover", (e) => onMarkerHover(id, { x: e.containerPoint.x, y: e.containerPoint.y }))
        .on("mouseout", () => onMarkerHover(null, null))
        .addTo(layer);
    }

    if (currentId) {
      const node = nodes.get(currentId);
      if (node) {
        const currentPos: [number, number] = [node.latitude, node.longitude];
        if (justEntered) {
          L.circleMarker(currentPos, {
            radius: 8,
            stroke: false,
            fill: true,
            fillColor: tokenColor("--color-info-500", "#2b86b7"),
            fillOpacity: 0.7,
            interactive: false,
            className: styles.pulseHalo,
            renderer: sharedSvg,
          }).addTo(layer);
        }
        L.circleMarker(currentPos, {
          radius: 8,
          color: tokenColor("--c-surface", "#ffffff"),
          weight: 3,
          fillColor: tokenColor("--color-info-500", "#2b86b7"),
          fillOpacity: 1,
          interactive: true,
          renderer: sharedSvg,
        })
          .on("click", () => onMarkerClick(currentId))
          .on("mouseover", () => onMarkerHover(currentId, null))
          .on("mouseout", () => onMarkerHover(null, null))
          .addTo(layer);
      }
    }

    return () => {
      layer.removeFrom(map.map);
    };
  }, [map, frame, path, routeLen, visitedIds, currentId, nodes, onMarkerClick, onMarkerHover]);

  /** Persistent start/goal pins: green + red, large markers (spec §12–§13). */
  const startGoalLayer = useMemo(() => (map ? L.layerGroup().addTo(map.map) : null), [map]);

  useEffect(() => {
    if (!startGoalLayer || !map) return;
    const addPin = (id: string | null, pinClass: string, label: string): L.Marker | null => {
      if (!id) return null;
      const node = nodes.get(id);
      if (!node) return null;
      const icon = L.divIcon({
        className: pinClass,
        html: `<span class="${styles.pin}"></span>`,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
        popupAnchor: [0, -13],
      });
      const marker = L.marker([node.latitude, node.longitude], {
        icon,
        keyboard: true,
        title: `${node.name} · ${label}`,
        alt: `${node.name} · ${label}`,
      });
      marker.on("click", () => onMarkerClick(node.id));
      marker.on("mouseover", () => onMarkerHover(node.id, null));
      marker.on("mouseout", () => onMarkerHover(null, null));
      marker.addTo(startGoalLayer);
      return marker;
    };
    const startPin = addPin(startId, styles.startPin, "Start");
    const goalPin = addPin(goalId, styles.goalPin, "Goal");
    return () => {
      if (startPin) startPin.remove();
      if (goalPin) goalPin.remove();
      startGoalLayer.removeFrom(map.map);
    };
  }, [map, nodes, startId, goalId, startGoalLayer, onMarkerClick, onMarkerHover]);

  return (
    <div
      data-testid="map-overlays"
      aria-hidden="true"
      data-visited={visitedIds.join(",")}
      data-current={currentId ?? ""}
      data-route={path ? String(routeLen) : ""}
      data-start={startId ?? ""}
      data-goal={goalId ?? ""}
    />
  );
}