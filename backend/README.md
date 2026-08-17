# HCMC Delivery Route Lab — backend

FastAPI backend for comparing classical search algorithms on a directed, contracted street graph in central Ho Chi Minh City. The product scenario is courier/delivery route planning: pair search, algorithm comparison, and multi-stop ordering. The search core uses standard-library Python and does not use NetworkX.

The bundled graph is an offline OpenStreetMap-derived snapshot. Traffic, travel time, flood susceptibility, disruption closures, and risk overlays are deterministic educational estimates, not live navigation data.

## Run locally

Python 3.11–3.13 is recommended.

~~~powershell
cd backend
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
~~~

OpenAPI is available at <http://127.0.0.1:8000/docs>. Run backend tests from this directory with:

~~~powershell
python -m pytest
~~~

## Canonical dataset

The default runtime file is:

<code>data/hcmc_delivery_osm_snapshot.json</code>

It contains:

- 1,103 nodes;
- 2,279 already-directed arcs;
- 187 delivery POIs, including 172 in the 992-node primary SCC;
- 85 strongly connected components in total;
- an OSM snapshot bounded to <code>[10.750, 106.665, 10.800, 106.715]</code>.

The 2,279 records must not be expanded. Source records labelled two-way already have a separate reverse row; the importer validates that reverse row and writes <code>bidirectional: false</code> for every canonical edge.

The small <code>data/delivery_teaching_fixture.json</code> file is only a deterministic API/test fixture. Override the runtime file with <code>ROUTING_DATASET_PATH</code> when needed.

## API

All public endpoints use the <code>/api/v1</code> prefix.

- <code>GET /health</code> — service and dataset readiness.
- <code>GET /metadata</code> — dataset, algorithm, heuristic, scenario, optimizer and trace registries.
- <code>GET /graph?scenario=normal&amp;compact=true</code> — topology/geometry with map-required attributes.
- <code>GET /graph?scenario=normal&amp;include_geojson=true</code> — also populate the duplicate GeoJSON FeatureCollection for GIS clients. Its feature list is empty by default to keep the browser payload smaller.
- <code>GET /traffic?scenario=heavy_rain</code> — lightweight per-edge overlay; no repeated nodes or geometry.
- <code>POST /search</code> — one pickup/drop-off route plus an optional alternative.
- <code>POST /compare</code> — run 2–8 algorithms under identical inputs.
- <code>POST /multi-route</code> — order several delivery stops with nearest-neighbor, Held–Karp, 2-opt, or seeded simulated annealing.

### Pair-search example

The canonical metadata recommends two primary-component POIs for a stable first run:

- <code>poi_way_152994798</code> — Co.op Mart;
- <code>poi_way_39514795</code> — Chợ Bến Thành.

~~~json
{
  "start_id": "poi_way_152994798",
  "goal_id": "poi_way_39514795",
  "algorithm": "astar",
  "heuristic": "travel_time",
  "scenario": "morning_rush",
  "cost_weights": {
    "distance": 0.25,
    "travel_time": 0.50,
    "traffic_delay": 0.20,
    "risk": 0.05
  },
  "include_trace": true,
  "max_trace_events": 1000,
  "max_expansions": 100000,
  "include_alternative": true
}
~~~

Algorithm IDs are <code>bfs</code>, <code>dfs</code>, <code>ucs</code>, <code>dijkstra</code>, <code>astar</code>, <code>greedy_best_first</code>, <code>bidirectional_dijkstra</code>, and <code>ida_star</code>.

Heuristic IDs are <code>zero</code>, <code>haversine</code>, <code>travel_time</code>, and <code>traffic_aware</code>. Metadata marks the first three admissible for their documented cost interpretation; traffic-aware intentionally demonstrates a practical heuristic that may overestimate.

Scenario IDs are <code>normal</code>, <code>morning_rush</code>, <code>evening_rush</code>, <code>heavy_rain</code>, and <code>incident</code>. The incident scenario is presented as a generic road disruption and closes only arcs carrying the corresponding synthetic flag.

Successful pair responses expose:

~~~text
request_id, status, found, start_id, goal_id,
algorithm, heuristic, scenario,
path, edge_ids, route_geojson,
metrics, trace, explanation, alternative, cost_breakdown
~~~

The ordered <code>edge_ids</code> array has exactly <code>len(path) - 1</code> items. Route geometry uses GeoJSON coordinate order <code>[longitude, latitude]</code>. The public cost invariant is <code>cost_breakdown.total_cost == metrics.path_cost</code>.

### Multi-stop example

~~~json
{
  "start_id": "poi_way_152994798",
  "stop_ids": [
    "poi_way_39514795",
    "poi_way_152990635"
  ],
  "method": "held_karp",
  "return_to_start": true,
  "scenario": "normal",
  "cost_weights": {
    "distance": 0.25,
    "travel_time": 0.50,
    "traffic_delay": 0.20,
    "risk": 0.05
  },
  "seed": 42,
  "max_iterations": 1000,
  "max_expansions": 100000
}
~~~

Held–Karp accepts at most 10 stops. Requests overall accept at most 12. Every pairwise leg uses Dijkstra under the selected scenario and weights.

## Canonical JSON contract

Required metadata fields are <code>id</code> and <code>name</code>. Nodes require <code>id</code>, <code>name</code>, <code>lat</code>, and <code>lon</code>. Edges require unique <code>id</code>, valid <code>source</code>/<code>target</code>, and positive <code>distance_m</code>.

~~~json
{
  "metadata": {
    "id": "hcmc-city-centre-delivery-osm-2026",
    "name": "Ho Chi Minh City Delivery Route Search Graph",
    "city": "Thành phố Hồ Chí Minh",
    "version": "2.0.0"
  },
  "nodes": [
    {
      "id": "poi_way_152994798",
      "name": "Co.op Mart",
      "kind": "delivery_supermarket",
      "lat": 10.7672833,
      "lon": 106.6861395,
      "attributes": {
        "delivery_destination": true,
        "delivery_category": "supermarket",
        "routing_component": "primary"
      }
    }
  ],
  "edges": [
    {
      "id": "hcmc_edge_0000",
      "source": "node-a",
      "target": "node-b",
      "distance_m": 120.0,
      "speed_kph": 35.0,
      "road_name": "Road name",
      "road_class": "secondary",
      "risk": 0.20,
      "traversable": true,
      "bidirectional": false,
      "attributes": {
        "source_direction": "one-way",
        "base_congestion": 2.4,
        "geometry": [[106.68, 10.77], [106.681, 10.771]]
      }
    }
  ]
}
~~~

Geometry is optional. The loader validates coordinate ranges, orients the polyline from source to target, and anchors both endpoints. It never reads from the temporary scrape directory.

## Importing the teammate export

The migration script is:

~~~powershell
python scripts/import_hcmc_snapshot.py
~~~

Default inputs:

- <code>backend/data-tmp/processed/graph.json</code>;
- <code>backend/data-tmp/raw/hcmc_overpass.json</code>.

Default output:

- <code>backend/data/hcmc_delivery_osm_snapshot.json</code>.

The input directory is intentionally git-ignored and is not a runtime package. The importer validates city, schema, unique IDs, endpoint references, direction pairs, coordinates, risk/congestion scales, time/speed reconstruction and graph size before writing the canonical snapshot. See <code>docs/DATASET.md</code> for exact provenance and measured statistics.

## Scope

The snapshot covers selected major roads and delivery POIs in a bounded central-HCMC area. It omits many local streets, alleys, turn restrictions and live access conditions. A route is an educational result on this snapshot, not turn-by-turn courier guidance.
