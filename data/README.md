# data

The **road graph** package: real OpenStreetMap road topology for HCMC city centre,
contracted into a directed teaching graph with deterministic synthetic traffic overlays.

* Final road graph: `data/processed/graph.json` (1103 nodes, 2279 directed edges).
* Raw OSM export (provenance): `data/raw/hcmc_overpass.json`.
* Schema: `data/models.py` (Node + Edge + GraphData). `SCHEMA_VERSION` is re-exported
  from `config/settings.py` (single source of truth).
* Loader: `data/loader.py` -> `load_graph()` -> `GraphData`, `load_metadata()` -> dict.
  The default path resolves to `data/processed/graph.json` via `config/paths.py`.

The derived POI-only **delivery graph** (`data/exports/delivery_graph.json`) is owned by
the `delivery/` package (see `docs/DELIVERY_GRAPH.md`).

Reproduce:

```bash
python scripts/fetch_overpass.py
python scripts/build_osm_snapshot.py
```

See `docs/DATASET_SPEC.md` for the full contract. Coordinate schema changes with the
algorithm and UI teams first.
