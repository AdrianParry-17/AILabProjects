# Dataset — Ho Chi Minh City Delivery Route Search Graph

This document describes the exact committed runtime graph, its one-time import path, provenance boundaries and known limitations.

## 1. Identity

| Field | Value |
|---|---|
| Canonical file | <code>backend/data/hcmc_delivery_osm_snapshot.json</code> |
| Dataset ID | <code>hcmc-city-centre-delivery-osm-2026</code> |
| Name | Ho Chi Minh City Delivery Route Search Graph |
| Version | <code>2.0.0</code> |
| City / country | Thành phố Hồ Chí Minh / Việt Nam |
| OSM base timestamp | <code>2026-08-05T16:31:02Z</code> |
| Source generation timestamp | <code>2026-08-05T17:35:43.919906+00:00</code> |
| Bounding box | south <code>10.750</code>, west <code>106.665</code>, north <code>10.800</code>, east <code>106.715</code> |
| Query selector | repository reconstruction at <code>scripts/overpass_hcmc.ql</code>; checksummed raw export is authoritative |
| License | ODbL 1.0 |
| Attribution | © OpenStreetMap contributors |

The bbox is a bounded central-HCMC teaching area, not the administrative boundary of the city.

## 2. What the query includes

The repository's reconstructed Overpass selector requests:

~~~overpass
[out:json][timeout:180];
(
  way["highway"~"^(primary|secondary|tertiary)(_link)?$"](10.750,106.665,10.800,106.715);
  nwr["amenity"~"^(hospital|university|marketplace|bus_station)$"](10.750,106.665,10.800,106.715);
  nwr["shop"="supermarket"](10.750,106.665,10.800,106.715);
);
(._;>;);
out body;
~~~

Consequences of this deliberate scope:

- local, residential, unclassified, alley, footway and most service-road topology is not queried as a road network;
- turn restrictions are not modeled;
- POI inclusion depends on OSM tags and the source snapshot timestamp;
- the query records only a bounded centre-city sample;
- rerunning the query later can produce different topology, names and counts because OSM is continuously edited.

Service-class arcs in the canonical graph are derived POI/access connectors from the source processing pipeline, not evidence that the query included the complete service-road network.

## 3. Runtime independence from temporary data

The teammate scrape is retained under <code>backend/data-tmp/</code>. That directory is intentionally git-ignored and must not be imported by application code.

The only supported migration path is:

~~~powershell
python scripts/import_hcmc_snapshot.py
~~~

Default inputs:

| Input | Role |
|---|---|
| <code>backend/data-tmp/processed/graph.json</code> | contracted source graph and educational overlay values |
| <code>backend/data-tmp/raw/hcmc_overpass.json</code> | raw OSM ways/tags used to recover explicit maxspeed provenance |

Default output:

<code>backend/data/hcmc_delivery_osm_snapshot.json</code>

FastAPI reads only the output file. Once the canonical snapshot exists, omitting the temporary directory does not affect runtime. The repository ignores the directory but does not delete the teammate's local files.

Recorded source checksums:

| Source | SHA-256 |
|---|---|
| Processed graph | <code>309798671DB1C7A29ACA7EEEA198C9E5903EAF8A71AED05F6DC47D9F690F41B1</code> |
| Raw Overpass export | <code>8F53BFF35B37E7B59234DEE15BB6CF14715C05460F80B0A568168A38009D60BD</code> |

These hashes identify the exact temporary inputs used for the committed canonical file. They are provenance records, not hashes of a future OSM refresh.

## 4. Import pipeline

~~~text
raw Overpass JSON ──┐
                    ├─ validate city/schema/IDs/coordinates
processed graph ────┘
          │
          ├─ rename latitude/longitude to lat/lon
          ├─ preserve every source row as exactly one directed arc
          ├─ move length_geometry to canonical geometry
          ├─ reconstruct and verify speed/time provenance
          ├─ normalize source risk by a fixed divisor of 5
          ├─ compute directed strongly connected components
          ├─ mark nodes primary or peripheral
          └─ write backend/data/hcmc_delivery_osm_snapshot.json
~~~

The importer fails instead of guessing when it encounters:

- a city other than Ho Chi Minh City;
- missing or duplicate IDs;
- an edge referencing an unknown endpoint;
- a self-loop;
- unsupported direction labels;
- invalid coordinates, distances, congestion or risk;
- a two-way-labelled arc without an explicit reverse record;
- a reconstructed travel time differing from source <code>time_min</code> by more than 0.01 minute;
- a graph smaller than the lab minimum.

## 5. Provenance by field

| Data | Origin | Canonical handling | Must not be claimed as |
|---|---|---|---|
| Road/POI coordinates and names | OSM snapshot | preserved after schema normalization | current ground truth |
| Highway class and OSM way IDs | OSM tags | preserved | complete access policy |
| Direction | processed OSM topology | each input row remains one directed arc | a turn-restriction model |
| Polyline geometry | processed OSM geometry | validated, oriented and endpoint-anchored | surveyed lane geometry |
| Explicit numeric maxspeed | raw OSM tag | minimum explicit value across all contracted ways when every referenced way has one | observed vehicle speed |
| Missing/symbolic maxspeed | derived | documented road-class fallback | OSM-provided speed |
| POI connector | derived by source pipeline | service arc retained with provenance | verified entrance or loading bay |
| Delivery category | OSM amenity/shop class | represented as a <code>delivery_*</code> node kind | a live customer order |
| Baseline congestion | synthetic source layer | preserved on a 1–5 scale | live traffic |
| Risk | synthetic source layer | fixed normalization <code>source_risk / 5</code> | measured crash or safety probability |
| Flood/disruption/closure flags | synthetic deterministic layer | used by scenarios | official alert or forecast |
| ETA and delay | derived/synthetic | distance, speed and scenario multiplier | turn-by-turn arrival guarantee |
| SCC/component label | canonical import analysis | computed from the exact directed arcs | permanent real-world reachability |

## 6. Graph inventory

### 6.1 Counts

| Metric | Count |
|---|---:|
| Raw OSM road ways reported by source | 2,008 |
| Stored road nodes | 916 |
| Delivery POIs | 187 |
| Canonical nodes | 1,103 |
| Canonical directed arcs | 2,279 |
| Source one-way-labelled arcs | 1,039 |
| Source two-way-labelled arcs | 1,240 |
| Parallel endpoint pairs | 4 |
| Strongly connected components | 85 |
| Largest SCC | 992 nodes |
| Delivery POIs in largest SCC | 172 |

The 2,279 edge records are already directed arcs. A source row labelled two-way has a separate reverse source row. The importer verifies the reverse exists and sets <code>bidirectional: false</code> on canonical rows so the backend loader does not expand the graph to 3,519 arcs.

### 6.2 Node kinds

| Kind | Count | Meaning |
|---|---:|---|
| <code>intersection</code> | 827 | retained road junction |
| <code>gateway</code> | 70 | boundary or terminal road node |
| <code>bridge_access</code> | 19 | retained bridge approach/access node |
| <code>delivery_hospital</code> | 52 | hospital-tagged candidate delivery POI |
| <code>delivery_supermarket</code> | 50 | supermarket candidate delivery POI |
| <code>delivery_university</code> | 40 | university candidate delivery POI |
| <code>delivery_market</code> | 35 | marketplace candidate delivery POI |
| <code>delivery_bus_station</code> | 10 | bus-station candidate delivery POI |

Hospitals are ordinary candidate delivery stops in this product. Their presence does not imply clinical capability, capacity, opening hours or suitability for medical use.

### 6.3 Road classes

| Canonical road class | Directed arcs |
|---|---:|
| <code>tertiary</code> | 776 |
| <code>primary</code> | 695 |
| <code>secondary</code> | 434 |
| <code>service</code> | 374 |

## 7. Directed connectivity

The canonical importer runs deterministic Kosaraju traversal over the exact 2,279 arcs and stores:

- <code>routing_component=primary</code> for nodes in the largest 992-node SCC;
- <code>routing_component=peripheral</code> for every other node.

Of 187 delivery POIs, 172 are in the primary SCC. Those 172 can reach one another in both directions under the base topology. The remaining 15 POIs are preserved for provenance and map visibility but are not guaranteed to support an arbitrary round trip.

Canonical metadata recommends two primary-component defaults:

| Role | ID | Name | Kind |
|---|---|---|---|
| Start | <code>poi_way_152994798</code> | Co.op Mart | <code>delivery_supermarket</code> |
| Goal | <code>poi_way_39514795</code> | Chợ Bến Thành | <code>delivery_market</code> |

Scenario closures can reduce reachability further. “No route” therefore describes the selected directed snapshot and scenario, not physical impossibility in the real city.

## 8. Geometry and direction

Canonical node coordinates use decimal degrees:

- <code>lat</code>: latitude;
- <code>lon</code>: longitude.

Edge geometry uses GeoJSON order:

<code>[[longitude, latitude], ...]</code>

On load, the backend validates every point, reverses a polyline when needed, and anchors its first and last positions to the source and target nodes. Route GeoJSON concatenates those oriented edge polylines.

Each canonical edge has one source and one target. <code>attributes.source_direction</code> preserves the source label, but route traversal follows the canonical row direction only. <code>bidirectional</code> is always false in this snapshot.

## 9. Speed and source-time reconstruction

For each contracted arc, the importer looks up all referenced OSM way IDs in the raw export.

1. If every referenced way has a parseable numeric maxspeed, it uses the minimum value.
2. Numeric mph is converted to km/h.
3. Symbolic or missing values trigger a road-class fallback.

Fallbacks:

| Road class | Speed |
|---|---:|
| primary | 45 km/h |
| secondary | 35 km/h |
| tertiary | 30 km/h |
| service | 20 km/h |
| unknown class | 25 km/h |

Measured provenance:

| Speed source | Arcs |
|---|---:|
| Minimum explicit OSM maxspeed across contracted ways | 624 |
| Tertiary fallback | 555 |
| Primary fallback | 470 |
| Service fallback | 374 |
| Secondary fallback | 256 |

The importer reconstructs:

<code>time_min = round(distance_km / speed_kph × 60, 2)</code>

and refuses the row if the result differs from source <code>time_min</code> by more than 0.01 minute. Seven very short arcs have a source time rounded to 0.00 minute; they still retain positive distance and speed and are not zero-cost edges.

Canonical speeds range from 20 to 70 km/h. They are tag-derived or documented defaults, not observed courier speeds.

## 10. Congestion, risk and traffic scenarios

### 10.1 Baseline congestion

The source congestion score uses a 1–5 educational scale. The importer stores it as:

- <code>attributes.base_congestion</code>;
- <code>attributes.source_congestion_score</code>.

The deterministic traffic model converts the score into a baseline multiplier and then applies the selected scenario. It is not a live congestion measurement.

### 10.2 Risk

The source uses a fixed 0–5 educational risk score. The canonical cost model requires a fraction, so conversion is always:

<code>canonical_risk = source_risk_score / 5</code>

The original score and divisor remain in attributes. The importer never normalizes by the observed dataset maximum, so a rebuild cannot silently rescale every route.

In the committed snapshot, canonical risk ranges from 0.06 to 0.66.

### 10.3 Scenarios

| ID | Interpretation |
|---|---|
| <code>normal</code> | snapshot baseline plus light deterministic variation |
| <code>morning_rush</code> | extra delay on major approaches |
| <code>evening_rush</code> | broader congestion and river-crossing pressure |
| <code>heavy_rain</code> | lower effective speed, with stronger bridge/risk effects |
| <code>incident</code> | generic road disruption; closes only explicitly flagged arcs |

Identical dataset, scenario and request inputs produce identical multipliers and route choices, apart from runtime measurement and generated request UUIDs.

## 11. Canonical schema

### 11.1 Metadata

| Field | Required | Meaning |
|---|---:|---|
| <code>id</code>, <code>name</code> | yes | stable dataset identity |
| <code>city</code>, <code>country</code>, <code>version</code> | yes for bundled file | display and version metadata |
| <code>source</code>, <code>source_url</code> | yes for bundled file | provenance |
| <code>bbox</code> | yes for bundled file | south/west/north/east |
| <code>osm_base_timestamp</code> | yes for bundled file | source snapshot time |
| <code>license</code>, <code>attribution</code> | yes for bundled file | OSM reuse terms |
| <code>stats</code> | yes for bundled file | measured counts, SCC data, checksums and defaults |

### 11.2 Nodes

| Field | Required | Notes |
|---|---:|---|
| <code>id</code> | yes | unique non-empty string |
| <code>name</code> | yes | non-empty display name |
| <code>kind</code> | no | defaults to intersection |
| <code>lat</code>, <code>lon</code> | yes | finite valid coordinates |
| <code>attributes</code> | no | OSM provenance, POI category and routing component |

Delivery POIs carry <code>delivery_destination=true</code> and <code>delivery_category</code>.

### 11.3 Edges

| Field | Required | Notes |
|---|---:|---|
| <code>id</code> | yes | unique directed-arc ID |
| <code>source</code>, <code>target</code> | yes | existing, distinct node IDs |
| <code>distance_m</code> | yes | finite and positive |
| <code>speed_kph</code> | no | finite and positive; bundled file always provides it |
| <code>road_name</code>, <code>road_class</code> | no | display/cost metadata |
| <code>risk</code> | no | canonical fraction in [0,1] |
| <code>traversable</code> | no | defaults true |
| <code>bidirectional</code> | no | false for every bundled arc |
| <code>attributes.geometry</code> | no | GeoJSON-order polyline |

The API exposes geometry in a dedicated edge field and removes the duplicate geometry entry from public attributes. A duplicate graph-wide GeoJSON FeatureCollection is returned only when <code>include_geojson=true</code>.

## 12. Validation and refresh procedure

For the existing teammate inputs:

~~~powershell
python scripts/import_hcmc_snapshot.py
cd backend
python -m pytest
~~~

For explicit paths, use one command:

~~~powershell
python scripts/import_hcmc_snapshot.py --input C:\path\to\processed\graph.json --raw-input C:\path\to\raw\hcmc_overpass.json --output backend\data\hcmc_delivery_osm_snapshot.json
~~~

Before accepting a refreshed snapshot:

1. Review metadata, bbox, source timestamp and OSM attribution.
2. Compare node, arc, POI, road-class and SCC counts.
3. Confirm every two-way-labelled source arc has an explicit reverse and runtime remains 2,279 only for the current snapshot.
4. Recheck geometry orientation and endpoint anchoring.
5. Review explicit/fallback speed provenance and time reconstruction.
6. Verify risk uses the fixed divisor of 5.
7. Run loader, API, algorithm, multi-stop and frontend tests.
8. Re-run performance measurements and regenerate route examples/screenshots.
9. Treat new hashes/counts as a new dataset version; do not copy the old evidence forward.

## 13. Known limitations

This dataset does not establish:

- complete street or alley coverage;
- legal or practical motorcycle access;
- turn restrictions, lane changes or loading zones;
- a verified entrance for every POI connector;
- current POI names, opening hours or operating status;
- live traffic, weather, flood or road-closure conditions;
- customer orders, vehicle capacity, time windows or courier position;
- guaranteed reachability outside the selected directed component/scenario;
- turn-by-turn navigation accuracy.

It supports an educational comparison of search and route-ordering algorithms on a documented, reproducible local snapshot. It must not be presented as a production navigation system.
