# visualization

Map/report serialization for graphs and routes (GeoJSON). No search logic.

```
geojson.py  # point_geometry, edge_geometry, route_to_geojson, graph_to_geojson
```

Consumed by `ui/` and future reports; it reads the shapes produced by `data/`,
`delivery/`, and `core/` without owning any algorithm.
