# delivery

The **application-layer delivery graph** package and the road shortest-path engine.

* `models.py` -> `DeliveryNode`, `DeliveryEdge`, `DeliveryGraph` (Pydantic).
  `SCHEMA_VERSION` is re-exported from `config/settings.py`.
* `road.py` -> `RoadGraph`: directed Dijkstra over `data.GraphData`
  (`dijkstra`, `shortest_path`, `edge`, `outgoing`).
* `builder.py` -> `build_delivery_graph(road, ...)` (MST + kNN) producing
  `data/exports/delivery_graph.json` (31 POIs / 70 directed edges). Build tuning
  (`DEFAULT_COUNTS`, `K_NEAREST`, ...) and paths come from `config/`.
* `loader.py` -> `load_delivery_graph()` / `load_delivery_metadata()`; the loader
  validates schema version, referential integrity, uniqueness, direction symmetry,
  minimums and strong connectivity on every call (`validate_delivery_graph`).
* `route.py` -> `expand_poi_path()` : POI path -> street-level polyline for the UI.

Reproduce:

```bash
python scripts/build_delivery_graph.py
```

See `docs/DELIVERY_GRAPH.md` for the full contract and `docs/ARCHITECTURE.md` for the
two-layer data model.
