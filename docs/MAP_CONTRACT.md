# MAP_CONTRACT.md

**HCMC Delivery AI Search - Frontend Map Data Contract**

Version: 2.0

Owner: Hưng (data/algorithm side)

Status: **Authoritative** (for the JSON payloads the React frontend consumes).

This document is the **contract only** between the data/algorithms layer and the React
frontend: what shapes, field names, and coordinate rules the UI depends on. It does not
specify React components, styling, state, or animation timing. The frontend is React.js
(`docs/ARCHITECTURE.md`); Streamlit is not used.

The Python side guarantees these shapes; the UI team renders them without touching data or
algorithm code.

---

# 1. What the frontend consumes

1. **A graph payload** — the POI-only **delivery graph** (`DeliveryGraph`,
   `data/exports/delivery_graph.json`) for the static map. Optionally the full road graph
   (`GraphData`) for a richer background.
2. **A `SearchResult` payload** — from any algorithm (BFS, DFS, UCS, A*, …) for result
   display and step-by-step animation.
3. **An expanded route payload** — street-level polyline for the highlighted route
   (produced by `delivery.route.expand_poi_path`, § 4).

All three use the same node-id scheme: node `id` is the shared key.

---

# 2. Graph payload (static layer)

The relevant shapes (from `delivery/models.py`, see `docs/DELIVERY_GRAPH.md`):

```json
{
  "metadata": { "id": "hcmc-delivery-graph-2026", "stats": { "poi_nodes": 31, "directed_edges": 70 } },
  "nodes": [
    { "id": "poi_way_750511344", "name": "Chợ Bến Thành", "latitude": 10.7723,
      "longitude": 106.6981, "kind": "delivery_market",
      "attributes": { "osm_type": "way", "osm_id": 750511344 } }
  ],
  "edges": [
    { "edge_id": "de_001", "start": "poi_way_750511344", "end": "poi_node_2141010789",
      "distance_km": 1.2, "time_min": 2.1, "congestion": 2.5, "risk": 1.0,
      "direction": "two-way", "road_path": ["poi_way_750511344", "osm_123", "osm_456"],
      "road_name": "Lê Lợi", "road_class": "secondary",
      "attributes": { "geometry": [[106.6981, 10.7723], [106.7010, 10.7760]] } }
  ]
}
```

## 2.1 What the map renders

| UI element | Source | Notes |
|------------|--------|-------|
| POI markers | `nodes[]` | `name` label, `latitude`/`longitude` position. |
| POI icon | `nodes[].kind` | style by delivery type (`delivery_*`). |
| Selection dropdowns | `nodes[]` | `start`, `destination`, optional intermediates. |
| POI-pair links | `edges[]` | draw between `start`/`end` node coords (delivery graph). |
| Route polyline (detail) | `edges[].attributes.geometry` | `[lon, lat]` road shape; optional. |
| Road background | `GET /road` (`GraphData`) | optional street-level rendering. |

## 2.2 Coordinate rules

* WGS84 (EPSG:4326), decimal degrees.
* Node coordinates are `latitude`, `longitude` fields. Geometry arrays use `[lon, lat]`.
* The dataset stores no pixel positions; the frontend projects lat/lon.
* Node `id` is stable and MUST NOT change once the UI depends on it.

---

# 3. SearchResult payload (dynamic layer)

Every algorithm returns the same shape (`core/search_result.py`):

```python
class SearchStep(BaseModel):
    current_node: str
    frontier: list[str]
    reason: str


class SearchResult(BaseModel):
    path: list[str]
    visited_nodes: list[str]
    steps: list[SearchStep]
    total_distance_km: float
    total_time_min: float
    total_cost: float
    processing_time_ms: float
    explanation: str
```

## 3.1 Field → UI mapping

| Field | Frontend use |
|-------|--------------|
| `path` | highlight the final route (POI ids in order). |
| `visited_nodes` | animate expanded/visited markers in order. |
| `steps` | drive the step-by-step animation (one frame per step). |
| `total_distance_km` | metrics panel "Tổng quãng đường". |
| `total_time_min` | metrics panel "Tổng thời gian ước tính". |
| `total_cost` | metrics panel "Tổng chi phí". |
| `processing_time_ms` | metrics panel "Thời gian xử lý (ms)". |
| `explanation` | explanation panel (Vietnamese). |

## 3.2 Step-by-step animation

Each `SearchStep` is one animation frame: highlight `current_node`, outline/show the
`frontier` ids, show `reason` as the caption. Frame order = `steps` order =
`visited_nodes` order. Every id in `path`/`visited_nodes`/`frontier`/`current_node` maps
to a node in the graph payload; unknown ids are a contract violation.

## 3.3 Edge cases the UI must tolerate

* `path == []` → no route; show `explanation`, no route polyline.
* `path == [start]` → start == goal; single-node route, no animation frames.
* `steps == []` → trivial search; show result without animation.

---

# 4. Expanded route payload (street-level detail)

The UI may request the road-level geometry for a POI path. Backend calls
`delivery.route.expand_poi_path(path, road_graph, delivery_graph)` and returns:

```json
{
  "node_ids": ["poi_way_750511344", "osm_123", "osm_456", "poi_node_2141010789"],
  "geometry": [[106.6981, 10.7723], [106.7010, 10.7760], [106.7040, 10.7790]],
  "hops": 3,
  "distance_km": 1.8,
  "time_min": 3.1
}
```

`geometry` is a `[lon, lat]` polyline drawn as the highlighted route. `hops` = number of
road segments. This lets the UI animate along real streets while keeping the algorithm
graph small.

> **Delivery to the frontend.** `expand_poi_path` returns the payload above. The GUI service
> (`ui/service/routing.py`) wraps `geometry` as a GeoJSON `Feature` (`route.geometry`) when it
> is embedded in the `/search` response (`GUI_ROADMAP §11`) — same `[lon,lat]` points, no field
> renaming.

---

# 5. Identifier rules (shared key)

* Node ids are strings (`poi_*`, `osm_*`), matching the dataset.
* The same strings appear in graph payloads, `SearchResult.path`,
  `SearchStep.current_node`, `SearchStep.frontier`, and expanded routes.
* The frontend never displays raw ids; it maps them to `name`.
* Ids are unique and case-sensitively consistent everywhere.

---

# 6. API delivery

Transport is JSON over HTTP (`docs/ARCHITECTURE.md § 6`). Conceptual endpoints:

| Method | Path | Returns |
|--------|------|---------|
| GET | `/dataset` | `DeliveryGraph` JSON (POI graph). |
| GET | `/road` | `GraphData` JSON (optional street background). |
| POST | `/search` | `SearchResult` JSON. |
| POST | `/route/expand` | expanded-route JSON (§ 4). |

No field renaming between Python and JSON. Both sides use the exact Pydantic field names.

The concrete endpoint surface served to the React frontend is defined by the GUI service in
`docs/GUI_ROADMAP.md §11` (`/graph`, `/search`, `/history`, `/algorithms`, `/health`,
`/version`, `/route`). The table above stays the conceptual contract between the
data/algorithms layer and the service; **payload shapes and field names in this document
always win.**

---

# 7. Contract checklist

- [ ] Delivery graph JSON field names match `delivery/models.py` exactly.
- [ ] `SearchResult`/`SearchStep` JSON field names match `core/search_result.py` exactly.
- [ ] Every id in algorithm output exists in the graph payload.
- [ ] Lat/lon present and valid for every node.
- [ ] Vietnamese names used for display.
- [ ] `kind` present on every node (delivery styling).
- [ ] `steps` order == `visited_nodes` expansion order.
- [ ] `path == []` behavior defined.
- [ ] No pixel coordinates in the dataset; frontend does projection.
- [ ] Expanded route geometry documented and stable.

---

# 8. Out of scope

React component structure, styling, state management, map library choice, animation
timing, playback controls. If the UI team needs different shapes, update this document
and agree with the data owner before any data/algorithm code changes.