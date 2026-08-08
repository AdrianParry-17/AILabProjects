# ROADMAP.md

**HCMC Delivery AI Search - Task Roadmap**

Version: 3.0

Owner: Hưng

Scope: tasks for **Hưng** in `Lab 1 - Searching.pdf` / `Lab_1_Plan.pdf`: dataset (crawl +
build), BFS, GUI/map support, and the report contribution. This roadmap is
dependency-ordered and written so the team and AI assistants know what to build, in what
order, and how to verify. It refers to the specs; it does not restate them.

---

## 0. Task summary

| # | Task | Deliverable | Spec |
|---|------|-------------|------|
| T1 | Crawl OSM + build road graph | `data/raw/*`, `data/processed/graph.json`, `scripts/` | `docs/DATASET_SPEC.md` |
| T2 | Build delivery graph | `delivery/`, `data/exports/delivery_graph.json` | `docs/DELIVERY_GRAPH.md` |
| T3 | Implement BFS + shared helpers | `algorithms/bfs.py`, `metrics.py`, `heuristic.py`, tests | `docs/BFS_SPEC.md`, `ALGORITHM_SPEC.md` |
| T4 | Lock the map contract | `GraphData` / `DeliveryGraph` / `SearchResult` / expanded route | `docs/MAP_CONTRACT.md` |
| T5 | Report contribution | dataset + BFS + comparison sections | assignment §4.9 |

---

## 1. Status at a glance

| Phase | Status |
|-------|--------|
| P1 Crawl & build road graph | DONE (1103 nodes / 2279 directed edges) |
| P2 Delivery graph | DONE (31 POIs / 70 directed edges, strongly connected) |
| P3 Shared cost/metrics helpers | DONE (`heuristic.py`, `metrics.py`) |
| P4 BFS + tests | DONE (`test_bfs.py`, 7 passing) |
| P5 Map contract + route expansion | contract + `delivery/route.py` done; API shell pending |
| P6 Report | in progress |
| P7 Final verification | pending |

---

## 2. P1 - Crawl & build road graph (DONE)

Pipeline (reproducible, see `docs/DATASET_SPEC.md § 6`):

1. `scripts/overpass_hcmc.ql` — Overpass query (bbox
   `10.7500,106.6650,10.8000,106.7150`; primary/secondary/tertiary + POIs).
2. `python scripts/fetch_overpass.py`
3. `python scripts/build_osm_snapshot.py`

Result: 1103 nodes (916 junctions + 187 POIs), 2279 directed edges. Real OSM topology and
names; congestion/risk are deterministic synthetic overlays (documented in metadata +
`DATASET_SPEC.md § 3`).

Done when: loads via `data.loader.load_graph()`; ≥ 20 nodes / ≥ 30 edges; connected; values
in range; metadata present.

---

## 3. P2 - Delivery graph (DONE)

`python scripts/build_delivery_graph.py`

Selects 4-6 POIs per kind, adds synthetic warehouse/airport nodes, and derives
POI-pair edges from road-graph shortest paths (MST + kNN). Result: 31 POIs / 70 directed
edges (60 two-way / 10 one-way), strongly connected. See `docs/DELIVERY_GRAPH.md`.

Done when: `delivery/loader.load_delivery_graph()` loads; invariants in
`DELIVERY_GRAPH.md § 5` hold; deterministic under fixed seed.

---

## 4. P3 - Shared helpers (DONE)

* `config/defaults.py` — `CostWeights` + `DEFAULT_WEIGHTS` (α .3, β .4, γ .2, δ .1);
  `algorithms/heuristic.py` — `edge_cost`.
* `algorithms/metrics.py` — `build_edge_lookup`, `path_metrics`, `path_total_cost`.
* `delivery/road.py` — `RoadGraph` Dijkstra (distance-only) used by the builder and route
  expansion.

These are consumed, not duplicated, by every algorithm (`ALGORITHM_SPEC.md § 3.2`, § 6).

---

## 5. P4 - BFS + tests (DONE)

`algorithms/bfs.py::bfs(graph, start, goal, enable_logging=True) -> SearchResult`
(registered as `BFSAlgorithm`, so `run_algorithm("bfs", ...)` also works).

Verification (`docs/BFS_SPEC.md § 6`):

- [x] `path[0]==start`, `path[-1]==goal`.
- [x] Directed edges honored on the delivery graph.
- [x] Disconnected pair → `path=[]`, non-crash.
- [x] `start==goal` → single-node path.
- [x] `steps` order == `visited_nodes` order.
- [x] By-hand trace test (`algorithms/test_bfs.py`).
- [x] `total_cost` from shared `edge_cost`; `processing_time_ms > 0`.

Follow-up: scenario where fewest-hop ≠ cheapest (report/demo example).

---

## 6. P5 - Map contract + route expansion

Goal: the UI renders the map and animates a search with zero data/algorithm churn.

- [x] `DeliveryGraph` / `SearchResult` / `SearchStep` JSON shapes locked
      (`docs/MAP_CONTRACT.md`).
- [x] `delivery/route.expand_poi_path` — POI path → road polyline.
- [ ] Backend API shell (`/dataset`, `/road`, `/search`, `/route/expand`) if a service
      layer is created (`ARCHITECTURE.md § 6`).
- [ ] UI team confirms it can draw the graph + animate a search from the payloads.

---

## 7. P6 - Report contribution

Per assignment §4.9 (dataset + BFS parts):

- **d. Dataset**: OSM crawling method, pipeline, POI lists, overlay rules, statistics,
  assumptions (`DATASET_SPEC.md`, `DELIVERY_GRAPH.md`).
- **e. Algorithm (BFS)**: principle, small worked example, completeness/optimality.
- **g. Comparison (BFS row)**: time/space complexity, nodes explored on the real dataset.

Bring the hop-vs-cost finding (P4) into the explanation.

---

## 8. P7 - Verification & handoff

- [ ] Road graph: loads, ≥ 20 nodes / ≥ 30 edges, connected, valid, metadata.
- [ ] Delivery graph: loads, ≥ 20 POIs / ≥ 30 edges, strongly connected, deterministic.
- [ ] BFS: correct `SearchResult`, by-hand test passes, merged with teammates' code.
- [ ] Contract: UI confirms rendering + single-search animation.
- [ ] Docs: `CONVENTION.md`, `ALGORITHM_SPEC.md`, `docs/*` mutually consistent.

---

## 9. Team calendar (from `Lab_1_Plan.pdf`)

| Window | Hưng | Milestone |
|--------|------|-----------|
| 4/8 - 7/8 | P1 (crawl+build), P2, P4 (BFS) | datasets built; BFS runs |
| Sat 8/8 | P1-P4 check-in | datasets loadable; BFS runs; output agreed |
| 8/8 - 10/8 | P4 (tests), P5 (handoff) | BFS tested; map contract handed to UI |
| 11/8 - 13/8 | P6 (report draft) | dataset + BFS sections drafted |
| 14/8 - 17/8 | P7 (verify + film) | verified, demo scenes ready |
| 18-19/8 | buffer | remaining fixes |

### 9.1 Priority when short of time

1. Datasets correct (P1, P2) — done.
2. BFS returns the right `SearchResult` (P4) — done.
3. BFS by-hand test (P4).
4. Contract handoff (P5).
5. Report content (P6).

---

## 10. Open items / risks

- **Backend/API**: the JSON service is a thin shell; if the UI team needs it early, build
  `/dataset` + `/search` before the rest.
- **Traffic scenarios**: rush-hour/rain multipliers are cost-layer work owned by the cost
  teammate; datasets are scenario-agnostic by design.
- **Crawl reproducibility**: mirrors can rate-limit; the stored `data/raw/` snapshot keeps
  the build reproducible offline.