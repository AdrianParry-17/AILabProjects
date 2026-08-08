import { memo, useEffect, useMemo } from "react";
import {
  CircleMarker,
  MapContainer,
  Pane,
  Polyline,
  Popup,
  TileLayer,
  Tooltip,
  useMap,
  useMapEvents,
} from "react-leaflet";
import { Activity, Crosshair, Layers3, MousePointerClick, Navigation, Route } from "lucide-react";
import type { GraphEdge, GraphPayload, MultiRouteResponse, SearchResponse, TraceStep } from "../types";
import { congestionColor } from "../lib/format";

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
}

function FitGraph({ graph }: { graph: GraphPayload }) {
  const map = useMap();
  const signature = graph.nodes.map((node) => `${node.lat},${node.lon}`).join("|");
  useEffect(() => {
    if (!graph.nodes.length) return;
    const bounds = graph.nodes.map((node) => [node.lat, node.lon] as [number, number]);
    map.fitBounds(bounds, { padding: [38, 38], maxZoom: 14 });
  }, [map, signature]);
  return null;
}

function NearestNodePicker({ graph, onSelect }: { graph: GraphPayload; onSelect: (id: string) => void }) {
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
}

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

const BaseRoadNetwork = memo(function BaseRoadNetwork({
  graph,
  nodeById,
}: {
  graph: GraphPayload;
  nodeById: Map<string, GraphPayload["nodes"][number]>;
}) {
  return (
    <Pane name="roads" style={{ zIndex: 410 }}>
      {graph.edges.map((edge, index) => {
        const positions = edgeCoordinates(edge, nodeById);
        if (positions.length < 2) return null;
        return (
          <Polyline
            key={edge.id || `${edge.source}-${edge.target}-${index}`}
            positions={positions}
            pathOptions={{
              color: congestionColor(edge.congestion, edge.closed),
              weight: edge.closed ? 4 : 2.4,
              opacity: edge.closed ? 0.8 : 0.46,
              dashArray: edge.closed ? "7 6" : undefined,
              className: "base-road-edge",
            }}
          >
            <Tooltip sticky opacity={0.96} className="road-tooltip">
              <strong>{edge.name || "Đường chưa đặt tên"}</strong><br />
              {Math.round(edge.distance_m)} m • mật độ {edge.congestion.toFixed(1)}/5
              {edge.flags?.length ? <><br />{edge.flags.join(" • ")}</> : null}
            </Tooltip>
          </Polyline>
        );
      })}
    </Pane>
  );
});

const BaseNodeLayer = memo(function BaseNodeLayer({
  graph,
  start,
  goal,
  stops,
  onSelectNode,
}: {
  graph: GraphPayload;
  start?: string;
  goal?: string;
  stops: string[];
  onSelectNode: (id: string) => void;
}) {
  return (
    <Pane name="graph-nodes" style={{ zIndex: 455 }}>
      {graph.nodes.map((node) => {
        const isStart = node.id === start;
        const isGoal = node.id === goal;
        const isStop = stops.includes(node.id);
        const accent = isStart
          ? "#34d399"
          : isGoal
            ? "#fb7185"
            : isStop
              ? "#c084fc"
              : node.is_hospital || node.kind === "hospital"
                ? "#f472b6"
                : "#a8b7ca";
        const radius = isStart || isGoal ? 8.5 : isStop ? 7.5 : node.is_hospital ? 6 : 4;
        return (
          <CircleMarker
            key={node.id}
            center={[node.lat, node.lon]}
            radius={radius}
            eventHandlers={{ click: (event) => { event.originalEvent.stopPropagation(); onSelectNode(node.id); } }}
            pathOptions={{
              color: "#06111f",
              weight: 2,
              fillColor: accent,
              fillOpacity: 0.96,
              className: `base-graph-node${isStart || isGoal || isStop ? " is-endpoint" : ""}`,
            }}
          >
            <Tooltip direction="top" offset={[0, -5]} opacity={0.98}>{node.name}</Tooltip>
            <Popup>
              <div className="node-popup">
                <strong>{node.name}</strong>
                <span>{node.kind.replaceAll("_", " ")} {node.district ? `• ${node.district}` : ""}</span>
                {node.address && <small>{node.address}</small>}
                <button type="button" onClick={() => onSelectNode(node.id)}>Chọn điểm này</button>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </Pane>
  );
}, (previous, next) => previous.graph === next.graph
  && previous.start === next.start
  && previous.goal === next.goal
  && previous.onSelectNode === next.onSelectNode
  && previous.stops.join("|") === next.stops.join("|"));

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
}: Props) {
  const nodeById = useMemo(() => new Map(graph?.nodes.map((node) => [node.id, node]) || []), [graph]);
  const edgeById = useMemo(() => new Map(graph?.edges.flatMap((edge) => edge.id ? [[edge.id, edge] as const] : []) || []), [graph]);
  const visited = new Set(traceStep?.visited || traceStep?.explored || []);
  const frontier = new Set(traceStep?.frontier || []);
  const discovered = new Set(traceStep?.newly_discovered || []);
  const revealResult = !traceStep || Boolean(traceStep.is_complete);
  const route = revealResult ? routeCoordinates(result) : [];
  const alternative = revealResult && "alternative" in (result || {})
    ? routeCoordinates((result as SearchResponse).alternative as unknown as SearchResponse)
    : [];

  const linkCoordinates = (link: { source: string; target: string; edge_id?: string }): [number, number][] => {
    const fromEdge = link.edge_id ? edgeCoordinates(edgeById.get(link.edge_id), nodeById) : [];
    if (fromEdge.length) return fromEdge;
    const source = nodeById.get(link.source);
    const target = nodeById.get(link.target);
    return source && target ? [[source.lat, source.lon], [target.lat, target.lon]] : [];
  };
  const exploredPaths = (traceStep?.explored_links || [])
    .map(linkCoordinates)
    .filter((positions) => positions.length > 1);
  const frontierPaths = (traceStep?.frontier_links || [])
    .map(linkCoordinates)
    .filter((positions) => positions.length > 1);
  let activePath = traceStep?.active_link ? linkCoordinates(traceStep.active_link) : [];
  if (!activePath.length && traceStep?.parent_id && traceStep.current) {
    const source = nodeById.get(traceStep.parent_id);
    const target = nodeById.get(traceStep.current);
    if (source && target) activePath = [[source.lat, source.lon], [target.lat, target.lon]];
  }

  const center: [number, number] = graph?.center
    ? [graph.center.lat, graph.center.lon]
    : [16.0678, 108.2208];
  const showTiles = String(import.meta.env.VITE_ENABLE_OSM_TILES ?? "true") !== "false";

  return (
    <section className="map-card panel" aria-label="Bản đồ mạng lưới giao thông">
      <div className="map-toolbar">
        <div>
          <span className="section-kicker">LIVE GRAPH CANVAS</span>
          <h2>Mạng lưới cấp cứu trung tâm Đà Nẵng</h2>
        </div>
        <div className="map-actions">
          <span><MousePointerClick size={14} /> {selectionLabel}</span>
          <span><Layers3 size={14} /> {graph?.nodes.length ?? 0} nút • {graph?.edges.length ?? 0} cung</span>
        </div>
      </div>

      <div className={`map-frame${traceStep ? " is-searching" : ""}`}>
        <MapContainer center={center} zoom={13} zoomControl attributionControl className="leaflet-map">
          {showTiles && (
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
              maxZoom={19}
            />
          )}
          {graph && <FitGraph graph={graph} />}
          {graph && <NearestNodePicker graph={graph} onSelect={onSelectNode} />}

          {graph && <BaseRoadNetwork graph={graph} nodeById={nodeById} />}

          <Pane name="search-tree" style={{ zIndex: 425 }}>
            {exploredPaths.length > 0 && (
              <Polyline
                positions={exploredPaths}
                pathOptions={{ color: "#20bde7", weight: 3.4, opacity: 0.62, className: "search-tree-explored" }}
              />
            )}
            {frontierPaths.length > 0 && (
              <Polyline
                positions={frontierPaths}
                pathOptions={{ color: "#fbbf24", weight: 2.7, opacity: 0.72, dashArray: "3 8", className: "search-tree-frontier" }}
              />
            )}
            {activePath.length > 1 && (
              <>
                <Polyline positions={activePath} pathOptions={{ color: "#03131f", weight: 11, opacity: 0.72, className: "search-edge-glow" }} />
                <Polyline positions={activePath} pathOptions={{ color: "#e8fbff", weight: 5, opacity: 1, dashArray: "10 8", className: "search-edge-active" }} />
              </>
            )}
          </Pane>

          <Pane name="route-result" style={{ zIndex: 440 }}>
            {alternative.length > 1 && (
              <Polyline positions={alternative} pathOptions={{ color: "#fbbf24", weight: 5, opacity: 0.7, dashArray: "7 9", className: "alternative-route" }} />
            )}
            {route.length > 1 && (
              <>
                <Polyline positions={route} pathOptions={{ color: "#001726", weight: 12, opacity: 0.64 }} />
                <Polyline positions={route} pathOptions={{ color: "#38d9ff", weight: 6, opacity: 0.98, className: "final-route" }} />
              </>
            )}
          </Pane>

          {graph && <BaseNodeLayer graph={graph} start={start} goal={goal} stops={stops} onSelectNode={onSelectNode} />}

          <Pane name="search-nodes" style={{ zIndex: 470 }}>
            {graph?.nodes.filter((node) => visited.has(node.id) || frontier.has(node.id) || discovered.has(node.id) || node.id === traceStep?.current).map((node) => {
              const isCurrent = node.id === traceStep?.current;
              const isFrontier = frontier.has(node.id);
              const isDiscovered = discovered.has(node.id);
              const accent = isCurrent ? "#ffffff" : isDiscovered ? "#a3e635" : isFrontier ? "#fbbf24" : "#38bdf8";
              return (
                <CircleMarker
                  key={`search-${node.id}`}
                  center={[node.lat, node.lon]}
                  radius={isCurrent ? 9.5 : isDiscovered ? 5.4 : isFrontier ? 4.5 : 3.2}
                  pathOptions={{
                    color: isCurrent ? "#38d9ff" : "#06111f",
                    weight: isCurrent ? 4 : 1.5,
                    fillColor: accent,
                    fillOpacity: isCurrent ? 1 : 0.84,
                    opacity: 1,
                    interactive: false,
                    className: isCurrent ? "search-node-active" : isDiscovered ? "search-node-new" : "search-node-state",
                  }}
                />
              );
            })}
          </Pane>
        </MapContainer>

        {loading && <div className="map-loading"><span className="spinner" /> Đang cập nhật traffic graph…</div>}
        {traceStep && (
          <div className={`search-hud${traceStep.is_complete ? traceStep.found === false ? " is-failed" : " is-complete" : ""}`} aria-live="polite">
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
