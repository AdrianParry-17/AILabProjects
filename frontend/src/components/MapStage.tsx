import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { canvas as createCanvasRenderer, circleMarker, DomEvent, layerGroup, polyline, type CircleMarker as LeafletCircleMarker, type Path, type PathOptions, type Renderer } from "leaflet";
import type { Polyline as LeafletPolyline } from "leaflet";
import {
  MapContainer,
  Pane,
  Polyline,
  TileLayer,
  useMap,
  useMapEvents,
} from "react-leaflet";
import { Activity, Crosshair, Layers3, MousePointerClick, Navigation, Route } from "lucide-react";
import type { GraphEdge, GraphPayload, MultiRouteResponse, SearchResponse, TraceLink, TraceStep } from "../types";
import { congestionColor, formatNodeKind } from "../lib/format";
import type { TrafficOverlay } from "../api";

interface Props {
  graph?: GraphPayload;
  result?: SearchResponse | MultiRouteResponse;
  traceStep?: TraceStep;
  start?: string;
  goal?: string;
  stops?: string[];
  selectionLabel: string;
  onSelectNode: (id: string) => void;
  loading?: boolean;
  trafficOverlay?: TrafficOverlay;
}

const FitGraph = memo(function FitGraph({ graph }: { graph: GraphPayload }) {
  const map = useMap();
  const signature = graph.bounds?.flat().join("|") || `${graph.name}|${graph.nodes.length}`;
  useEffect(() => {
    if (!graph.nodes.length) return;
    const bounds = graph.bounds || graph.nodes.map((node) => [node.lat, node.lon] as [number, number]);
    map.fitBounds(bounds, { padding: [38, 38], maxZoom: 14 });
  }, [map, signature]);
  return null;
});

const FocusSearch = memo(function FocusSearch({
  graph,
  start,
  goal,
  stops,
  active,
}: {
  graph: GraphPayload;
  start?: string;
  goal?: string;
  stops: string[];
  active: boolean;
}) {
  const map = useMap();
  const wasActive = useRef(false);
  const selectionKey = [start, goal, ...stops].filter(Boolean).join("|");
  useEffect(() => {
    if (active) {
      const selected = new Set([start, goal, ...stops].filter(Boolean));
      const bounds = graph.nodes
        .filter((node) => selected.has(node.id))
        .map((node) => [node.lat, node.lon] as [number, number]);
      if (bounds.length >= 2) map.fitBounds(bounds, { padding: [105, 105], maxZoom: 15, animate: false });
      wasActive.current = true;
    } else if (wasActive.current) {
      const bounds = graph.bounds || graph.nodes.map((node) => [node.lat, node.lon] as [number, number]);
      map.fitBounds(bounds, { padding: [38, 38], maxZoom: 14, animate: false });
      wasActive.current = false;
    }
  }, [active, graph, map, selectionKey]);
  return null;
});

const NearestNodePicker = memo(function NearestNodePicker({ graph, onSelect }: { graph: GraphPayload; onSelect: (id: string) => void }) {
  useMapEvents({
    click(event) {
      let best: { id: string; score: number } | undefined;
      const latitudeScale = Math.cos((event.latlng.lat * Math.PI) / 180);
      for (const node of graph.nodes) {
        const dy = node.lat - event.latlng.lat;
        const dx = (node.lon - event.latlng.lng) * latitudeScale;
        const score = dx * dx + dy * dy;
        if (!best || score < best.score) best = { id: node.id, score };
      }
      if (best) onSelect(best.id);
    },
  });
  return null;
});

function routeCoordinates(result?: SearchResponse | MultiRouteResponse): [number, number][] {
  const coordinates = result?.route_geojson?.geometry?.coordinates || [];
  return coordinates.map(([lon, lat]) => [lat, lon]);
}

function edgeCoordinates(
  edge: GraphEdge | undefined,
  nodeById: Map<string, GraphPayload["nodes"][number]>,
): [number, number][] {
  if (!edge) return [];
  if (edge.geometry?.length) return edge.geometry.map(([lon, lat]) => [lat, lon]);
  const source = nodeById.get(edge.source);
  const target = nodeById.get(edge.target);
  return source && target ? [[source.lat, source.lon], [target.lat, target.lon]] : [];
}

function tracePaths(
  edgeIds: string[] | undefined,
  links: TraceLink[] | undefined,
  coordinatesByEdgeId: Map<string, [number, number][]>,
  nodeById: Map<string, GraphPayload["nodes"][number]>,
): Map<string, [number, number][]> {
  const paths = new Map<string, [number, number][]>();
  if (edgeIds?.length) {
    for (const edgeId of edgeIds) {
      const positions = coordinatesByEdgeId.get(edgeId);
      if (positions?.length && !paths.has(`edge:${edgeId}`)) paths.set(`edge:${edgeId}`, positions);
    }
    return paths;
  }
  for (const link of links || []) {
    const key = link.edge_id ? `edge:${link.edge_id}` : `link:${link.source}>${link.target}`;
    if (paths.has(key)) continue;
    const fromEdge = link.edge_id ? coordinatesByEdgeId.get(link.edge_id) : undefined;
    if (fromEdge?.length) {
      paths.set(key, fromEdge);
      continue;
    }
    const source = nodeById.get(link.source);
    const target = nodeById.get(link.target);
    if (source && target) paths.set(key, [[source.lat, source.lon], [target.lat, target.lon]]);
  }
  return paths;
}

const SearchTreeLayer = memo(function SearchTreeLayer({
  traceStep,
  coordinatesByEdgeId,
  nodeById,
  renderer,
}: {
  traceStep?: TraceStep;
  coordinatesByEdgeId: Map<string, [number, number][]>;
  nodeById: Map<string, GraphPayload["nodes"][number]>;
  renderer: Renderer;
}) {
  const map = useMap();
  const exploredGroupRef = useRef<ReturnType<typeof layerGroup> | null>(null);
  const frontierGroupRef = useRef<ReturnType<typeof layerGroup> | null>(null);
  const exploredRef = useRef(new Map<string, LeafletPolyline>());
  const frontierRef = useRef(new Map<string, LeafletPolyline>());

  useEffect(() => {
    const exploredGroup = layerGroup().addTo(map);
    const frontierGroup = layerGroup().addTo(map);
    exploredGroupRef.current = exploredGroup;
    frontierGroupRef.current = frontierGroup;
    return () => {
      exploredGroup.remove();
      frontierGroup.remove();
      exploredGroupRef.current = null;
      frontierGroupRef.current = null;
      exploredRef.current.clear();
      frontierRef.current.clear();
    };
  }, [map]);

  useEffect(() => {
    const syncPaths = (
      current: Map<string, LeafletPolyline>,
      group: ReturnType<typeof layerGroup> | null,
      desired: Map<string, [number, number][]>,
      options: PathOptions,
      behind: boolean,
    ) => {
      if (!group) return;
      for (const [key, path] of current) {
        if (desired.has(key)) continue;
        group.removeLayer(path);
        current.delete(key);
      }
      for (const [key, positions] of desired) {
        if (current.has(key)) continue;
        const path = polyline(positions, { ...options, pane: "search-tree", renderer, interactive: false }).addTo(group);
        if (behind) path.bringToBack();
        current.set(key, path);
      }
    };

    syncPaths(
      exploredRef.current,
      exploredGroupRef.current,
      tracePaths(traceStep?.explored_edge_ids, traceStep?.explored_links, coordinatesByEdgeId, nodeById),
      { color: "#20bde7", weight: 3.4, opacity: 0.62 },
      true,
    );
    syncPaths(
      frontierRef.current,
      frontierGroupRef.current,
      tracePaths(traceStep?.frontier_edge_ids, traceStep?.frontier_links, coordinatesByEdgeId, nodeById),
      { color: "#fbbf24", weight: 2.7, opacity: 0.72, dashArray: "3 8" },
      false,
    );
  }, [coordinatesByEdgeId, nodeById, renderer, traceStep]);

  return null;
});

const BaseRoadNetwork = memo(function BaseRoadNetwork({
  graph,
  nodeById,
  renderer,
  trafficOverlay,
  onReady,
}: {
  graph: GraphPayload;
  nodeById: Map<string, GraphPayload["nodes"][number]>;
  renderer: Renderer;
  trafficOverlay?: TrafficOverlay;
  onReady: () => void;
}) {
  const map = useMap();
  const topologyKey = `${graph.name}|${graph.generated_at || "snapshot"}|${graph.nodes.length}|${graph.edges.length}`;
  const displayRoads = useMemo(() => {
    const reciprocalRoads = new Map<string, { visualId: string; edge: GraphEdge; memberIds: string[] }>();
    const roads: { visualId: string; edge: GraphEdge; memberIds: string[] }[] = [];
    graph.edges.forEach((edge, index) => {
      const edgeId = edge.id || `${edge.source}-${edge.target}-${index}`;
      if (edge.direction !== "two_way") {
        roads.push({ visualId: edgeId, edge, memberIds: [edgeId] });
        return;
      }
      const endpoints = [edge.source, edge.target].sort().join("|");
      const key = `${endpoints}|${edge.name}|${edge.distance_m.toFixed(3)}`;
      const existing = reciprocalRoads.get(key);
      if (existing) {
        existing.memberIds.push(edgeId);
      } else {
        const road = { visualId: edgeId, edge, memberIds: [edgeId] };
        reciprocalRoads.set(key, road);
        roads.push(road);
      }
    });
    return roads;
  }, [topologyKey]);
  const roadMembers = useMemo(() => new Map(displayRoads.map((road) => [road.visualId, road.memberIds])), [displayRoads]);
  const roadMembersRef = useRef(roadMembers);
  roadMembersRef.current = roadMembers;
  const conditions = useMemo(() => new Map(graph.edges.map((edge, index) => [edge.id || `${edge.source}-${edge.target}-${index}`, edge])), [graph.edges]);
  const conditionsRef = useRef(conditions);
  conditionsRef.current = conditions;
  const overlay = useMemo(
    () => new Map((trafficOverlay?.edges || []).map((status) => [status.edge_id, status])),
    [trafficOverlay],
  );
  const overlayRef = useRef(overlay);
  overlayRef.current = overlay;
  const pathsRef = useRef(new Map<string, Path>());
  const roadState = useCallback((visualId: string) => {
    const memberIds = roadMembersRef.current.get(visualId) || [visualId];
    const edges = memberIds.map((edgeId) => conditionsRef.current.get(edgeId)).filter(Boolean) as GraphEdge[];
    const closed = memberIds.some((edgeId) => overlayRef.current.get(edgeId)?.closed ?? Boolean(conditionsRef.current.get(edgeId)?.closed));
    const level = Math.max(1, ...memberIds.map((edgeId) => {
      const edge = conditionsRef.current.get(edgeId);
      return overlayRef.current.get(edgeId)?.level ?? edge?.congestion ?? 1;
    }));
    return { edge: edges[0], closed, level, memberCount: memberIds.length };
  }, []);
  const roadStyle = useCallback((visualId: string): PathOptions => {
    const state = roadState(visualId);
    return {
      pane: "roads",
      renderer,
      color: congestionColor(state.level, state.closed),
      weight: state.closed ? 4 : 2.4,
      opacity: state.closed ? 0.8 : 0.46,
      dashArray: state.closed ? "7 6" : undefined,
    };
  }, [renderer, roadState]);

  const wireRoadPath = useCallback((visualId: string, path: Path) => {
    path.bindTooltip(() => {
      const state = roadState(visualId);
      const edge = state.edge;
      const root = document.createElement("div");
      const title = document.createElement("strong");
      title.textContent = edge?.name || "Đường chưa đặt tên";
      root.append(title, document.createElement("br"));
      root.append(`${Math.round(edge?.distance_m || 0)} m • mật độ ${state.level.toFixed(1)}/5`);
      if (state.memberCount > 1) root.append(document.createElement("br"), "Hai chiều • hiển thị mức ảnh hưởng cao hơn");
      const flags = [...(edge?.flags || [])];
      if (state.closed) flags.push("có chiều đang tạm đóng");
      if (flags.length) root.append(document.createElement("br"), flags.join(" • "));
      return root;
    }, { sticky: true, opacity: 0.96, className: "road-tooltip" });
    pathsRef.current.set(visualId, path);
    path.on("mouseover", () => {
      const closed = roadState(visualId).closed;
      path.setStyle({ weight: closed ? 5 : 3.5, opacity: 0.86 });
    });
    path.on("mouseout", () => {
      path.setStyle(roadStyle(visualId));
    });
  }, [roadState, roadStyle]);

  useEffect(() => {
    const pane = map.getPane("roads") || map.createPane("roads");
    pane.style.zIndex = "410";
    const group = layerGroup().addTo(map);
    pathsRef.current.clear();
    let index = 0;
    let frame = 0;
    let cancelled = false;

    const addRoadsWithinFrameBudget = () => {
      if (cancelled) return;
      const frameDeadline = performance.now() + 6;
      let added = 0;
      while (index < displayRoads.length && (added < 12 || performance.now() < frameDeadline)) {
        const road = displayRoads[index];
        const positions = edgeCoordinates(road.edge, nodeById);
        index += 1;
        if (positions.length < 2) continue;
        const path = polyline(positions, roadStyle(road.visualId)).addTo(group);
        wireRoadPath(road.visualId, path);
        added += 1;
      }
      if (index < displayRoads.length) frame = window.requestAnimationFrame(addRoadsWithinFrameBudget);
      else frame = window.requestAnimationFrame(onReady);
    };

    if (displayRoads.length) frame = window.requestAnimationFrame(addRoadsWithinFrameBudget);
    else frame = window.requestAnimationFrame(onReady);
    return () => {
      cancelled = true;
      window.cancelAnimationFrame(frame);
      group.remove();
      pathsRef.current.clear();
    };
  }, [displayRoads, map, nodeById, onReady, renderer, roadStyle, topologyKey, wireRoadPath]);

  useEffect(() => {
    // Leaflet's Canvas renderer coalesces same-tick setStyle calls into one redraw.
    // Spreading these calls across RAFs forces repeated near-full-network paints.
    for (const [edgeId, path] of pathsRef.current) path.setStyle(roadStyle(edgeId));
  }, [conditions, overlay, roadStyle]);

  return null;
});

const BaseNodeLayer = memo(function BaseNodeLayer({
  graph,
  start,
  goal,
  stops,
  onSelectNode,
  renderer,
  onReady,
}: {
  graph: GraphPayload;
  start?: string;
  goal?: string;
  stops: string[];
  onSelectNode: (id: string) => void;
  renderer: Renderer;
  onReady: () => void;
}) {
  const map = useMap();
  const topologyKey = `${graph.name}|${graph.generated_at || "snapshot"}|${graph.nodes.length}|${graph.edges.length}`;
  const markersRef = useRef(new Map<string, LeafletCircleMarker>());
  const selectionRef = useRef({ start, goal, stops: new Set(stops) });
  selectionRef.current = { start, goal, stops: new Set(stops) };
  const onSelectRef = useRef(onSelectNode);
  onSelectRef.current = onSelectNode;
  const deliveryNodes = useMemo(() => graph.nodes.filter((node) => node.is_delivery_point), [topologyKey]);
  const markerAppearance = useCallback((nodeId: string) => {
    const selected = selectionRef.current;
    const isStart = nodeId === selected.start;
    const isGoal = nodeId === selected.goal;
    const isStop = selected.stops.has(nodeId);
    return {
      radius: isStart || isGoal ? 8.5 : isStop ? 7.5 : 5.5,
      style: {
        color: "#06111f",
        weight: 2,
        fillColor: isStart ? "#34d399" : isGoal ? "#fb7185" : isStop ? "#c084fc" : "#f472b6",
        fillOpacity: 0.96,
      },
    };
  }, []);

  useEffect(() => {
    const pane = map.getPane("graph-nodes") || map.createPane("graph-nodes");
    pane.style.zIndex = "455";
    const group = layerGroup().addTo(map);
    markersRef.current.clear();
    let index = 0;
    let frame = 0;
    let cancelled = false;
    const addNodesWithinFrameBudget = () => {
      if (cancelled) return;
      const frameDeadline = performance.now() + 4;
      let added = 0;
      while (index < deliveryNodes.length && (added < 8 || performance.now() < frameDeadline)) {
        const node = deliveryNodes[index];
        index += 1;
        const appearance = markerAppearance(node.id);
        const marker = circleMarker([node.lat, node.lon], {
          pane: "graph-nodes",
          renderer,
          bubblingMouseEvents: false,
          radius: appearance.radius,
          ...appearance.style,
        }).addTo(group);
        markersRef.current.set(node.id, marker);
        marker.bindTooltip(node.name || "Giao lộ chưa đặt tên", { direction: "top", offset: [0, -5], opacity: 0.98 });
        const popup = document.createElement("div");
        popup.className = "node-popup";
        const title = document.createElement("strong");
        title.textContent = node.name || "Giao lộ chưa đặt tên";
        const kind = document.createElement("span");
        kind.textContent = `${formatNodeKind(node.kind)}${node.district ? ` • ${node.district}` : ""}`;
        popup.append(title, kind);
        if (node.address) {
          const address = document.createElement("small");
          address.textContent = node.address;
          popup.append(address);
        }
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = "Chọn điểm này";
        button.addEventListener("click", (event) => {
          event.stopPropagation();
          onSelectRef.current(node.id);
        });
        popup.append(button);
        marker.bindPopup(popup);
        marker.on("click", (event: any) => {
          if (event.originalEvent) DomEvent.stopPropagation(event.originalEvent);
          onSelectRef.current(node.id);
        });
        added += 1;
      }
      if (index < deliveryNodes.length) frame = window.requestAnimationFrame(addNodesWithinFrameBudget);
      else frame = window.requestAnimationFrame(onReady);
    };
    if (deliveryNodes.length) frame = window.requestAnimationFrame(addNodesWithinFrameBudget);
    else frame = window.requestAnimationFrame(onReady);
    return () => {
      cancelled = true;
      window.cancelAnimationFrame(frame);
      group.remove();
      markersRef.current.clear();
    };
  }, [deliveryNodes, map, markerAppearance, onReady, renderer, topologyKey]);

  useEffect(() => {
    const markers = [...markersRef.current.entries()];
    let index = 0;
    let frame = 0;
    let cancelled = false;
    const updateNodesWithinFrameBudget = () => {
      if (cancelled) return;
      const frameDeadline = performance.now() + 4;
      let updated = 0;
      while (index < markers.length && (updated < 12 || performance.now() < frameDeadline)) {
        const [nodeId, marker] = markers[index];
        const appearance = markerAppearance(nodeId);
        marker.setRadius(appearance.radius);
        marker.setStyle(appearance.style);
        index += 1;
        updated += 1;
      }
      if (index < markers.length) frame = window.requestAnimationFrame(updateNodesWithinFrameBudget);
    };
    frame = window.requestAnimationFrame(updateNodesWithinFrameBudget);
    return () => {
      cancelled = true;
      window.cancelAnimationFrame(frame);
    };
  }, [goal, markerAppearance, start, stops]);

  return null;
}, (previous, next) => previous.graph === next.graph
  && previous.start === next.start
  && previous.goal === next.goal
  && previous.renderer === next.renderer
  && previous.onSelectNode === next.onSelectNode
  && previous.stops.join("|") === next.stops.join("|"));

const SearchNodeLayer = memo(function SearchNodeLayer({
  graph,
  traceStep,
  start,
  goal,
  stops,
  renderer,
}: {
  graph?: GraphPayload;
  traceStep?: TraceStep;
  start?: string;
  goal?: string;
  stops: string[];
  renderer: Renderer;
}) {
  const map = useMap();
  const groupRef = useRef<ReturnType<typeof layerGroup> | null>(null);
  const markersRef = useRef(new Map<string, LeafletCircleMarker>());
  const markerVisualRef = useRef(new Map<string, string>());
  const nodeById = useMemo(() => new Map(graph?.nodes.map((node) => [node.id, node]) || []), [graph]);

  useEffect(() => {
    const group = layerGroup().addTo(map);
    groupRef.current = group;
    return () => {
      group.remove();
      groupRef.current = null;
      markersRef.current.clear();
      markerVisualRef.current.clear();
    };
  }, [map]);

  useEffect(() => {
    const group = groupRef.current;
    if (!group || !graph) return;
    const visited = new Set(traceStep?.visited || traceStep?.explored || []);
    const frontier = new Set(traceStep?.frontier || []);
    const discovered = new Set(traceStep?.newly_discovered || []);
    const stopSet = new Set(stops);
    const visible = new Set<string>([
      ...visited,
      ...frontier,
      ...discovered,
      ...(traceStep?.current ? [traceStep.current] : []),
      ...(start ? [start] : []),
      ...(goal ? [goal] : []),
      ...stops,
    ]);
    for (const [nodeId, marker] of markersRef.current) {
      if (!visible.has(nodeId)) {
        group.removeLayer(marker);
        markersRef.current.delete(nodeId);
        markerVisualRef.current.delete(nodeId);
      }
    }
    for (const nodeId of visible) {
      const node = nodeById.get(nodeId);
      if (!node) continue;
      const isCurrent = nodeId === traceStep?.current;
      const isFrontier = frontier.has(nodeId);
      const isDiscovered = discovered.has(nodeId);
      const isStart = nodeId === start;
      const isGoal = nodeId === goal;
      const isStop = stopSet.has(nodeId);
      const accent = isCurrent ? "#ffffff" : isStart ? "#34d399" : isGoal ? "#fb7185" : isStop ? "#c084fc" : isDiscovered ? "#a3e635" : isFrontier ? "#fbbf24" : "#38bdf8";
      const radius = isCurrent ? 9.5 : isStart || isGoal ? 8.5 : isStop ? 7.5 : isDiscovered ? 5.4 : isFrontier ? 4.5 : 3.2;
      const visualKey = `${accent}|${radius}|${isCurrent ? 1 : 0}`;
      let marker = markersRef.current.get(nodeId);
      if (!marker) {
        marker = circleMarker([node.lat, node.lon], {
          pane: "search-nodes",
          renderer,
          interactive: false,
        }).addTo(group);
        markersRef.current.set(nodeId, marker);
      }
      if (markerVisualRef.current.get(nodeId) === visualKey) continue;
      marker.setRadius(radius);
      marker.setStyle({
        color: isCurrent ? "#38d9ff" : "#06111f",
        weight: isCurrent ? 4 : 1.5,
        fillColor: accent,
        fillOpacity: isCurrent ? 1 : 0.84,
        opacity: 1,
      });
      markerVisualRef.current.set(nodeId, visualKey);
    }
  }, [goal, graph, nodeById, renderer, start, stops, traceStep]);

  return null;
});

export function MapStage({
  graph,
  result,
  traceStep,
  start,
  goal,
  stops = [],
  selectionLabel,
  onSelectNode,
  loading,
  trafficOverlay,
}: Props) {
  const topologyKey = graph ? `${graph.name}|${graph.generated_at || "snapshot"}|${graph.nodes.length}|${graph.edges.length}` : "empty";
  const [roadsReadyFor, setRoadsReadyFor] = useState("");
  const [nodesReadyFor, setNodesReadyFor] = useState("");
  const markRoadsReady = useCallback(() => setRoadsReadyFor(topologyKey), [topologyKey]);
  const markNodesReady = useCallback(() => setNodesReadyFor(topologyKey), [topologyKey]);
  const baseLayersReady = Boolean(graph && roadsReadyFor === topologyKey && nodesReadyFor === topologyKey);
  const topologyNodes = useMemo(() => graph?.nodes || [], [topologyKey]);
  const nodeById = useMemo(() => new Map(topologyNodes.map((node) => [node.id, node])), [topologyNodes]);
  const edgeById = useMemo(() => new Map(graph?.edges.flatMap((edge) => edge.id ? [[edge.id, edge] as const] : []) || []), [graph]);
  const coordinatesByEdgeId = useMemo(() => new Map(
    [...edgeById].map(([edgeId, edge]) => [edgeId, edgeCoordinates(edge, nodeById)] as const),
  ), [edgeById, nodeById]);
  const roadRenderer = useMemo(() => createCanvasRenderer({ pane: "roads", padding: 0.35 }), []);
  const nodeRenderer = useMemo(() => createCanvasRenderer({ pane: "graph-nodes", padding: 0.35 }), []);
  const searchRenderer = useMemo(() => createCanvasRenderer({ pane: "search-nodes", padding: 0.35 }), []);
  const searchTreeRenderer = useMemo(() => createCanvasRenderer({ pane: "search-tree", padding: 0.35 }), []);
  const visited = new Set(traceStep?.visited || traceStep?.explored || []);
  const frontier = new Set(traceStep?.frontier || []);
  const revealResult = !traceStep || Boolean(traceStep.is_complete);
  const route = revealResult ? routeCoordinates(result) : [];
  const alternative = revealResult && "alternative" in (result || {})
    ? routeCoordinates((result as SearchResponse).alternative as unknown as SearchResponse)
    : [];

  const linkCoordinates = (link: TraceLink): [number, number][] => {
    const fromEdge = link.edge_id ? coordinatesByEdgeId.get(link.edge_id) : undefined;
    if (fromEdge?.length) return fromEdge;
    const source = nodeById.get(link.source);
    const target = nodeById.get(link.target);
    return source && target ? [[source.lat, source.lon], [target.lat, target.lon]] : [];
  };
  let activePath = traceStep?.active_link ? linkCoordinates(traceStep.active_link) : [];
  if (!activePath.length && traceStep?.parent_id && traceStep.current) {
    const source = nodeById.get(traceStep.parent_id);
    const target = nodeById.get(traceStep.current);
    if (source && target) activePath = [[source.lat, source.lon], [target.lat, target.lon]];
  }
  if (traceStep?.is_complete) activePath = [];

  const center: [number, number] = graph?.center
    ? [graph.center.lat, graph.center.lon]
    : [10.7769, 106.6951];
  const showTiles = String(import.meta.env.VITE_ENABLE_OSM_TILES ?? "true") !== "false";

  return (
    <section className="map-card panel" aria-label="Bản đồ mạng lưới giao thông">
      <div className="map-toolbar">
        <div>
          <span className="section-kicker">LIVE GRAPH CANVAS</span>
          <h2>Mạng lưới giao nhận trung tâm {graph?.city || "TP.HCM"}</h2>
        </div>
        <div className="map-actions">
          <span><MousePointerClick size={14} /> {selectionLabel}</span>
          <span><Layers3 size={14} /> {graph?.nodes.length ?? 0} nút • {graph?.edges.length ?? 0} cung</span>
        </div>
      </div>

      <div
        className={`map-frame${traceStep ? " is-searching" : ""}`}
        data-base-layers-ready={baseLayersReady ? "true" : "false"}
      >
        <MapContainer center={center} zoom={13} zoomControl attributionControl className="leaflet-map">
          {showTiles && (
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
              maxZoom={19}
            />
          )}
          {graph && <FitGraph graph={graph} />}
          {graph && <FocusSearch graph={graph} start={start} goal={goal} stops={stops} active={Boolean(traceStep)} />}
          {graph && <NearestNodePicker graph={graph} onSelect={onSelectNode} />}

          {graph && <BaseRoadNetwork graph={graph} nodeById={nodeById} renderer={roadRenderer} trafficOverlay={trafficOverlay} onReady={markRoadsReady} />}

          <Pane name="search-tree" style={{ zIndex: 425 }}>
            <SearchTreeLayer
              key={topologyKey}
              traceStep={traceStep}
              coordinatesByEdgeId={coordinatesByEdgeId}
              nodeById={nodeById}
              renderer={searchTreeRenderer}
            />
          </Pane>

          <Pane name="search-active" style={{ zIndex: 430 }}>
            {activePath.length > 1 && (
              <>
                <Polyline positions={activePath} className="search-edge-glow" interactive={false} pathOptions={{ color: "#03131f", weight: 11, opacity: 0.72 }} />
                <Polyline positions={activePath} className="search-edge-active" interactive={false} pathOptions={{ color: "#e8fbff", weight: 5, opacity: 1, dashArray: "10 8" }} />
              </>
            )}
          </Pane>

          <Pane name="route-result" style={{ zIndex: 440 }}>
            {alternative.length > 1 && (
              <Polyline positions={alternative} className="alternative-route" interactive={false} pathOptions={{ color: "#fbbf24", weight: 5, opacity: 0.7, dashArray: "7 9" }} />
            )}
            {route.length > 1 && (
              <>
                <Polyline positions={route} interactive={false} pathOptions={{ color: "#001726", weight: 12, opacity: 0.64 }} />
                <Polyline positions={route} className="final-route" interactive={false} pathOptions={{ color: "#38d9ff", weight: 6, opacity: 0.98 }} />
              </>
            )}
          </Pane>

          {graph && <BaseNodeLayer graph={graph} start={start} goal={goal} stops={stops} onSelectNode={onSelectNode} renderer={nodeRenderer} onReady={markNodesReady} />}

          <Pane name="search-nodes" style={{ zIndex: 470 }}>
            <SearchNodeLayer graph={graph} traceStep={traceStep} start={start} goal={goal} stops={stops} renderer={searchRenderer} />
          </Pane>
        </MapContainer>

        {(loading || (graph && !baseLayersReady)) && <div className="map-loading"><span className="spinner" /> Đang cập nhật mạng giao thông…</div>}
        {traceStep && (
          <div className={`search-hud${traceStep.is_complete ? traceStep.found === false ? " is-failed" : " is-complete" : ""}`} aria-live={traceStep.is_complete ? "polite" : "off"}>
            <div className="search-hud-title">
              {traceStep.is_complete ? <Route size={15} /> : <Activity size={15} />}
              <span>{traceStep.is_complete ? traceStep.found === false ? "Không tìm thấy tuyến" : "Đã dựng tuyến" : traceStep.phase === "start" ? "Khởi tạo tìm kiếm" : "Đang mở rộng cây tìm kiếm"}</span>
            </div>
            <strong>{traceStep.current_name || "Giao lộ đang xét"}</strong>
            <div className="search-hud-stats">
              <span><b>{traceStep.explored_count ?? visited.size}</b> đã mở rộng</span>
              <span><b>{traceStep.frontier_size ?? frontier.size}</b> frontier</span>
              {Number.isFinite(traceStep.f_score) && <span><b>{traceStep.f_score?.toFixed(2)}</b> f-score</span>}
            </div>
          </div>
        )}
        <div className="map-compass"><Navigation size={16} /><span>Bắc</span></div>
        <div className="map-hint"><Crosshair size={15} /> Bấm bản đồ để chọn giao lộ gần nhất</div>
        <div className={`map-legend${traceStep ? " trace-legend" : ""}`}>
          {traceStep ? (
            <>
              <span><i style={{ background: "#20bde7" }} /> Cây đã khám phá</span>
              <span><i style={{ background: "#fbbf24" }} /> Frontier</span>
              <span><i style={{ background: "#ffffff" }} /> Cạnh đang xét</span>
            </>
          ) : (
            <>
              <span><i style={{ background: "#34d399" }} /> Thoáng</span>
              <span><i style={{ background: "#facc15" }} /> Đông</span>
              <span><i style={{ background: "#fb923c" }} /> Tắc</span>
              <span><i style={{ background: "#ef4444" }} /> Nguy cơ/đóng</span>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
